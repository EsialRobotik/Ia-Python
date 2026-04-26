"""
Simulateur 2D pour robot - Affichage de la table de jeu.
Utilise PySide6 pour le rendu SVG natif.
"""

import ast
import html as html_module
import json
import math
import os
import re
import socket
import sys
import time
from datetime import datetime

from PySide6.QtCore import QRectF, QPointF, QTimer, QElapsedTimer, Qt, QLocale, QObject, QThread, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QPixmap, QFont
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QComboBox, QLabel, QPushButton,
    QGridLayout, QDoubleSpinBox, QCheckBox, QTextEdit,
    QFileDialog, QSlider,
)

# Chemin du dossier simulation, relatif à ce fichier
SIMULATION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "")

# Plage d'années supportées
YEAR_MIN = 2022
YEAR_MAX = datetime.now().year

# Couleurs des traces par robot (cyclique)
ROBOT_TRAIL_COLORS = [
    QColor(0, 150, 255),    # bleu
    QColor(50, 200, 50),    # vert
    QColor(255, 222, 33),   # jaune
    QColor(0, 200, 200),    # cyan
    QColor(255, 100, 100),  # rouge clair
    QColor(200, 100, 255),  # violet
]

# Paramètres d'animation
ANIM_INTERVAL_MS = 16        # ~60 FPS
ANIM_ROTATION_SPEED = 3.0   # radians / seconde
ANIM_MOVE_SPEED = 1500.0     # unités table / seconde (1 unité = 1 mm → 1.5 m/s)


def normalize_angle(angle: float) -> float:
    """Normalise un angle dans l'intervalle ]-π, π]."""
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle <= -math.pi:
        angle += 2 * math.pi
    return angle


def get_available_years():
    """Retourne la liste des années pour lesquelles un fichier table.svg existe."""
    years = []
    for year in range(YEAR_MIN, YEAR_MAX + 1):
        svg_path = os.path.join(SIMULATION_DIR, str(year), "table.svg")
        if os.path.isfile(svg_path):
            years.append(str(year))
    return years


def get_table_svg_path(year: str) -> str:
    """Retourne le chemin absolu du fichier table.svg pour une année donnée."""
    return os.path.join(SIMULATION_DIR, year, "table.svg")


def get_table_size(year: str) -> tuple[int, int] | None:
    """
    Lit table.json et retourne (largeur, hauteur) en pixels.
    sizeY = largeur, sizeX = hauteur.
    Retourne None si le fichier n'existe pas.
    """
    json_path = os.path.join(SIMULATION_DIR, year, "table.json")
    if not os.path.isfile(json_path):
        return None
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["sizeY"], data["sizeX"]


def load_table_zones(year: str) -> tuple[list, list]:
    """
    Lit table.json et retourne (forbiddenZones, dynamicZones).
    Retourne deux listes vides si le fichier n'existe pas.
    """
    json_path = os.path.join(SIMULATION_DIR, year, "table.json")
    if not os.path.isfile(json_path):
        return [], []
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("forbiddenZones", []), data.get("dynamicZones", [])


def load_robots(year: str) -> list[dict]:
    """
    Lit init.json et retourne la liste des robots avec leur pixmap chargé.
    Chaque élément contient : id, x, y, theta, regX, regY, pixmap.
    Retourne une liste vide si le fichier n'existe pas.
    """
    json_path = os.path.join(SIMULATION_DIR, year, "init.json")
    if not os.path.isfile(json_path):
        return []
    with open(json_path, "r", encoding="utf-8") as f:
        robots_data = json.load(f)

    robots = []
    for robot in robots_data:
        img_path = os.path.join(SIMULATION_DIR, year, robot["src"])
        pixmap = QPixmap(img_path)
        if pixmap.isNull():
            continue
        robots.append({
            "id": robot["id"],
            "x": robot["x"],
            "y": robot["y"],
            "theta": robot.get("theta", 0),
            "regX": robot.get("regX", 0),
            "regY": robot.get("regY", 0),
            "pixmap": pixmap,
        })
    return robots


class TableWidget(QWidget):
    """
    Widget affichant le SVG de la table en conservant le ratio d'aspect.
    L'image s'inscrit entièrement dans l'espace disponible (largeur ET hauteur),
    centrée, sans déformation.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._renderer = QSvgRenderer(self)
        self._grid_renderer = QSvgRenderer(self)
        self._table_size = None
        self._forbidden_zones: list = []
        self._dynamic_zones: list = []
        self._show_forbidden = False
        self._show_dynamic = False
        self._robots: list[dict] = []
        self._speed_factor: float = 1.0  # multiplicateur de vitesse d'animation

        # Zoom et panoramique
        self._zoom = 1.0
        self._pan = QPointF(0.0, 0.0)
        self._panning = False
        self._pan_start = QPointF()

        # Cache du fond (SVG + zones) — invalide quand zoom/pan/zones changent
        self._bg_cache: QPixmap | None = None

        # Traces persistantes : liste de (x1, y1, x2, y2, QColor) en coords table
        self._trails: list[tuple[float, float, float, float, QColor]] = []
        self._active_trails: dict[int, tuple] = {}  # robot_idx → trace en cours

        # Animation — une file et une étape courante par robot
        self._anim_queues: dict[int, list[dict]] = {}    # robot_idx → steps en attente
        self._anim_currents: dict[int, dict] = {}        # robot_idx → étape en cours
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._anim_tick)
        # Horloge globale démarrée une fois — jamais remise à zéro
        self._global_clock = QElapsedTimer()
        self._global_clock.start()

        # Détections temps réel : liste de {x, y, color, expire} en coords table
        self._detections: list[dict] = []
        self._detection_cleanup_timer = QTimer(self)
        self._detection_cleanup_timer.setInterval(100)
        self._detection_cleanup_timer.timeout.connect(self._cleanup_detections)

    def load(self, path: str, table_size: tuple[int, int] | None = None):
        """
        Charge un fichier SVG.
        table_size : (largeur, hauteur) lues depuis table.json, ou None pour
                     utiliser les dimensions par défaut du SVG.
        """
        self._renderer.load(path)
        grid_path = os.path.join(SIMULATION_DIR, "grid.svg")
        self._grid_renderer.load(grid_path)
        self._table_size = table_size
        self._zoom = 1.0
        self._pan = QPointF(0.0, 0.0)
        self._bg_cache = None
        self._speed_factor = 1.0
        self._trails.clear()
        self._active_trails.clear()
        self._anim_queues.clear()
        self._anim_currents.clear()
        self._anim_timer.stop()
        self.update()

    def set_zones(self, forbidden: list, dynamic: list):
        """Définit les zones interdites et dynamiques à dessiner."""
        self._forbidden_zones = forbidden
        self._dynamic_zones = dynamic
        for zone in self._dynamic_zones:
            zone["_init_active"] = zone.get("active", True)
        self._bg_cache = None
        self.update()

    def set_show_forbidden(self, visible: bool):
        self._show_forbidden = visible
        self._bg_cache = None
        self.update()

    def set_show_dynamic(self, visible: bool):
        self._show_dynamic = visible
        self._bg_cache = None
        self.update()

    def set_robots(self, robots: list[dict]):
        """Définit la liste des robots à dessiner et assigne une couleur de trace."""
        self._robots = robots
        for i, robot in enumerate(robots):
            robot["trail_color"] = ROBOT_TRAIL_COLORS[i % len(ROBOT_TRAIL_COLORS)]
            # Mémoriser la position de départ pour le reset
            robot["init_x"] = robot["x"]
            robot["init_y"] = robot["y"]
            robot["init_theta"] = robot["theta"]
        self.update()

    def _get_svg_size(self) -> tuple[int, int]:
        """Retourne (largeur, hauteur) du SVG, en tenant compte de table.json."""
        if self._table_size is not None:
            return self._table_size
        size = self._renderer.defaultSize()
        return size.width(), size.height()

    def _compute_transform(self) -> tuple[float, float, float]:
        """
        Calcule les paramètres de transformation pour le rendu.
        Intègre le zoom et le panoramique.
        Retourne (scale, offset_x, offset_y).
        _pan est un décalage en pixels écran appliqué après le centrage et le zoom.
        """
        svg_w, svg_h = self._get_svg_size()
        if svg_w <= 0 or svg_h <= 0:
            return 1.0, 0.0, 0.0

        widget_w, widget_h = self.width(), self.height()
        base_scale = min(widget_w / svg_w, widget_h / svg_h)
        scale = base_scale * self._zoom

        offset_x = (widget_w - svg_w * scale) / 2 + self._pan.x()
        offset_y = (widget_h - svg_h * scale) / 2 + self._pan.y()
        return scale, offset_x, offset_y

    def _to_screen(self, json_x: float, json_y: float, scale: float,
                   offset_x: float, offset_y: float) -> QPointF:
        """
        Convertit les coordonnées table (JSON) en coordonnées écran.
        Dans le repère table : X vers le bas, Y vers la droite.
        Dans le repère écran (Qt/SVG) : x vers la droite, y vers le bas.
        Donc : screen_x = json_y, screen_y = json_x.
        """
        return QPointF(offset_x + json_y * scale, offset_y + json_x * scale)

    def _draw_zones(self, painter: QPainter, zones: list, color: QColor,
                    scale: float, offset_x: float, offset_y: float):
        """Dessine une liste de zones avec la couleur donnée (semi-transparente)."""
        fill_color = QColor(color)
        fill_color.setAlpha(80)
        border_color = QColor(color)
        border_color.setAlpha(180)

        painter.setPen(QPen(border_color, 2))
        painter.setBrush(QBrush(fill_color))

        label_font = QFont("Sans", 8)
        label_color = QColor(0, 0, 0)

        for zone in zones:
            if not zone.get("active", True):
                continue

            forme = zone.get("forme", "")
            center_pt = None

            if forme == "polygone":
                points = zone.get("points", [])
                if len(points) < 3:
                    continue
                polygon = QPolygonF([
                    self._to_screen(p["x"], p["y"], scale, offset_x, offset_y)
                    for p in points
                ])
                painter.drawPolygon(polygon)
                cx = sum(p["x"] for p in points) / len(points)
                cy = sum(p["y"] for p in points) / len(points)
                center_pt = self._to_screen(cx, cy, scale, offset_x, offset_y)

            elif forme == "cercle":
                centre = zone.get("centre", {})
                rayon = zone.get("rayon", 0)
                center_pt = self._to_screen(
                    centre.get("x", 0), centre.get("y", 0),
                    scale, offset_x, offset_y
                )
                r_scaled = rayon * scale
                painter.drawEllipse(center_pt, r_scaled, r_scaled)

            label = zone.get("desc") or zone.get("id", "")
            if label and center_pt is not None:
                painter.save()
                painter.setFont(label_font)
                fm = painter.fontMetrics()
                text_width = fm.horizontalAdvance(label)
                text_height = fm.height()
                padding = 4
                bg_rect = QRectF(
                    center_pt.x() - text_width / 2 - padding,
                    center_pt.y() - text_height / 2 - padding,
                    text_width + 2 * padding,
                    text_height + 2 * padding,
                )
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(255, 255, 255, 200))
                painter.drawRoundedRect(bg_rect, 3, 3)
                painter.setPen(label_color)
                painter.setBrush(Qt.NoBrush)
                painter.drawText(bg_rect, Qt.AlignCenter, label)
                painter.restore()

    # --- Détections temps réel ------------------------------------------------

    _DETECTION_DISPLAY_RADIUS = 200   # mm — rayon du cercle affiché
    _DETECTION_DEDUP_RADIUS_SQ = 150 * 150  # mm² — seuil de déduplication spatiale
    _DETECTION_LIFETIME = 1.0         # secondes

    def add_detection(self, x: float, y: float, color: QColor):
        """
        Ajoute une détection d'obstacle à afficher pendant 1 s.
        Si une détection de même couleur existe déjà à moins de 150 mm,
        son timer est simplement rafraîchi (évite de surcharger l'affichage).
        """
        now = time.monotonic()
        expire = now + self._DETECTION_LIFETIME
        for det in self._detections:
            if det["color"].name() == color.name():
                dx = det["x"] - x
                dy = det["y"] - y
                if dx * dx + dy * dy <= self._DETECTION_DEDUP_RADIUS_SQ:
                    det["expire"] = expire
                    return
        self._detections.append({"x": x, "y": y, "color": QColor(color), "expire": expire})
        if not self._detection_cleanup_timer.isActive():
            self._detection_cleanup_timer.start()
        self.update()

    def _cleanup_detections(self):
        """Retire les détections expirées et arrête le timer si la liste est vide."""
        now = time.monotonic()
        before = len(self._detections)
        self._detections = [d for d in self._detections if d["expire"] > now]
        if not self._detections:
            self._detection_cleanup_timer.stop()
        if len(self._detections) != before:
            self.update()

    def _draw_detections(self, painter: QPainter, scale: float,
                         offset_x: float, offset_y: float):
        """Dessine les cercles de détection semi-transparents."""
        now = time.monotonic()
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        for det in self._detections:
            if det["expire"] <= now:
                continue
            color = QColor(det["color"])
            color.setAlpha(160)
            painter.setBrush(QBrush(color))
            center = self._to_screen(det["x"], det["y"], scale, offset_x, offset_y)
            r = self._DETECTION_DISPLAY_RADIUS * scale
            painter.drawEllipse(center, r, r)
        painter.restore()

    def _draw_robots(self, painter: QPainter, scale: float,
                     offset_x: float, offset_y: float):
        """
        Dessine les robots sur la table.
        Les axes de l'image sont dans le même sens que la table (X bas, Y droite).
        En coordonnées pixel de l'image : pixel_x = Y (droite), pixel_y = X (bas).
        Le swap d'axes table→écran inverse le sens de rotation, d'où le -theta.
        """
        for robot in self._robots:
            # Position du point de référence en coordonnées écran
            screen_x = offset_x + robot["y"] * scale  # table Y (droite) → écran x
            screen_y = offset_y + robot["x"] * scale  # table X (bas)    → écran y

            # regX est dans la direction X de l'image (bas) = pixel y
            # regY est dans la direction Y de l'image (droite) = pixel x
            img_ref_px = robot["regY"]  # pixel x = direction droite = regY
            img_ref_py = robot["regX"]  # pixel y = direction bas    = regX

            painter.save()
            painter.translate(screen_x, screen_y)
            painter.rotate(-math.degrees(robot["theta"]))
            painter.scale(scale, scale)
            painter.drawPixmap(int(-img_ref_px), int(-img_ref_py), robot["pixmap"])
            painter.restore()

            # Point centré sur la position (x, y) du robot, couleur = trace du robot
            dot_color = robot.get("trail_color", QColor(255, 255, 0))
            painter.save()
            painter.setPen(QPen(dot_color.darker(150), 1))
            painter.setBrush(QBrush(dot_color))
            painter.drawEllipse(QPointF(screen_x, screen_y), 5, 5)
            painter.restore()

    # --- Traces persistantes ---------------------------------------------------

    def _draw_trails(self, painter: QPainter, scale: float,
                     offset_x: float, offset_y: float):
        """Dessine les traces de déplacement (lignes persistantes + trace en cours)."""
        all_trails = list(self._trails) + list(self._active_trails.values())
        for x1, y1, x2, y2, color in all_trails:
            p1 = self._to_screen(x1, y1, scale, offset_x, offset_y)
            p2 = self._to_screen(x2, y2, scale, offset_x, offset_y)
            painter.setPen(QPen(color, 2))
            painter.drawLine(p1, p2)

    # --- Animation -------------------------------------------------------------

    def animate_robot_move(self, robot_id: str, target_x: float, target_y: float,
                           target_theta: float, trail_color: QColor):
        """
        Enfile les étapes d'animation d'un robot : rotation vers la cible,
        déplacement, puis rotation vers l'angle final.
        Chaque robot a sa propre file — tous les robots s'animent en parallèle.
        """
        robot_idx = next(
            (i for i, r in enumerate(self._robots) if r["id"] == robot_id), None
        )
        if robot_idx is None:
            return

        robot = self._robots[robot_idx]
        dx = target_x - robot["x"]
        dy = target_y - robot["y"]
        distance = math.sqrt(dx * dx + dy * dy)

        queue = self._anim_queues.setdefault(robot_idx, [])

        queue.append({"type": "rotate", "to_theta": target_theta})

        if distance > 1:
            queue.append({
                "type": "move",
                "to_x": target_x,
                "to_y": target_y,
                "trail_color": QColor(trail_color),
            })

        # Démarrer l'étape suivante pour ce robot s'il est inactif
        if robot_idx not in self._anim_currents:
            self._start_next_anim(robot_idx)

        if not self._anim_timer.isActive():
            self._anim_timer.start(ANIM_INTERVAL_MS)

    def animate_robot_orbital(self, robot_id: str, degrees: float, forward: bool,
                              on_right_wheel: bool, trail_color: QColor):
        """Enfile une animation de rotation orbitale autour d'une roue codeuse."""
        robot_idx = next(
            (i for i, r in enumerate(self._robots) if r["id"] == robot_id), None
        )
        if robot_idx is None:
            return

        queue = self._anim_queues.setdefault(robot_idx, [])
        queue.append({
            "type": "orbital",
            "degrees": degrees,
            "forward": forward,
            "on_right_wheel": on_right_wheel,
            "trail_color": QColor(trail_color),
        })

        if robot_idx not in self._anim_currents:
            self._start_next_anim(robot_idx)
        if not self._anim_timer.isActive():
            self._anim_timer.start(ANIM_INTERVAL_MS)

    def _start_next_anim(self, robot_idx: int):
        """Démarre la prochaine étape de la file du robot donné."""
        queue = self._anim_queues.get(robot_idx, [])
        if not queue:
            self._anim_currents.pop(robot_idx, None)
            return

        step = queue.pop(0)
        robot = self._robots[robot_idx]

        if step["type"] == "rotate":
            from_theta = robot["theta"]
            diff = normalize_angle(step["to_theta"] - from_theta)
            if abs(diff) < 0.01:
                self._start_next_anim(robot_idx)
                return
            self._anim_currents[robot_idx] = {
                "type": "rotate",
                "from_theta": from_theta,
                "to_theta": from_theta + diff,
                "duration": abs(diff) / ANIM_ROTATION_SPEED,
                "start_time": self._global_clock.elapsed(),
            }

        elif step["type"] == "move":
            from_x, from_y = robot["x"], robot["y"]
            to_x, to_y = step["to_x"], step["to_y"]
            dist = math.sqrt((to_x - from_x) ** 2 + (to_y - from_y) ** 2)
            self._anim_currents[robot_idx] = {
                "type": "move",
                "from_x": from_x, "from_y": from_y,
                "to_x": to_x, "to_y": to_y,
                "duration": max(dist / (ANIM_MOVE_SPEED * self._speed_factor), 0.05),
                "start_time": self._global_clock.elapsed(),
                "trail_color": step.get("trail_color"),
            }

        elif step["type"] == "orbital":
            pivot_offset = robot.get("pivotOffset", 132.45)
            theta = robot["theta"]
            degrees = step["degrees"]
            forward = step["forward"]
            on_right_wheel = step["on_right_wheel"]
            angle_rad = math.radians(degrees)

            if on_right_wheel:
                cx = robot["x"] + pivot_offset * math.sin(theta)
                cy = robot["y"] - pivot_offset * math.cos(theta)
                rot = -angle_rad if forward else angle_rad
            else:
                cx = robot["x"] - pivot_offset * math.sin(theta)
                cy = robot["y"] + pivot_offset * math.cos(theta)
                rot = angle_rad if forward else -angle_rad

            # Angle polaire de départ (robot par rapport au pivot)
            start_angle = math.atan2(robot["y"] - cy, robot["x"] - cx)
            arc_length = pivot_offset * abs(rot)
            self._anim_currents[robot_idx] = {
                "type": "orbital",
                "center_x": cx, "center_y": cy,
                "radius": pivot_offset,
                "from_angle": start_angle,
                "rot": rot,
                "from_theta": theta,
                "duration": max(arc_length / (ANIM_MOVE_SPEED * self._speed_factor), 0.05),
                "start_time": self._global_clock.elapsed(),
                "trail_color": step.get("trail_color"),
                "prev_x": robot["x"], "prev_y": robot["y"],
            }

    def _anim_tick(self):
        """Fait avancer toutes les animations actives en parallèle."""
        if not self._anim_currents:
            self._anim_timer.stop()
            return

        for robot_idx, anim in list(self._anim_currents.items()):
            elapsed = (self._global_clock.elapsed() - anim["start_time"]) / 1000.0
            t = min(elapsed / anim["duration"], 1.0)
            robot = self._robots[robot_idx]

            if anim["type"] == "rotate":
                robot["theta"] = anim["from_theta"] + (anim["to_theta"] - anim["from_theta"]) * t

            elif anim["type"] == "move":
                robot["x"] = anim["from_x"] + (anim["to_x"] - anim["from_x"]) * t
                robot["y"] = anim["from_y"] + (anim["to_y"] - anim["from_y"]) * t
                if anim.get("trail_color"):
                    self._active_trails[robot_idx] = (
                        anim["from_x"], anim["from_y"],
                        robot["x"], robot["y"],
                        anim["trail_color"],
                    )

            elif anim["type"] == "orbital":
                angle = anim["from_angle"] + anim["rot"] * t
                prev_x, prev_y = robot["x"], robot["y"]
                robot["x"] = anim["center_x"] + anim["radius"] * math.cos(angle)
                robot["y"] = anim["center_y"] + anim["radius"] * math.sin(angle)
                robot["theta"] = anim["from_theta"] + anim["rot"] * t
                if anim.get("trail_color"):
                    # Persister chaque petit segment pour dessiner l'arc
                    self._trails.append((
                        prev_x, prev_y,
                        robot["x"], robot["y"],
                        anim["trail_color"],
                    ))

            if t >= 1.0:
                if anim["type"] == "move" and anim.get("trail_color"):
                    self._trails.append((
                        anim["from_x"], anim["from_y"],
                        anim["to_x"], anim["to_y"],
                        anim["trail_color"],
                    ))
                    self._active_trails.pop(robot_idx, None)
                self._start_next_anim(robot_idx)

        self.update()

    def reset(self):
        """Remet les robots à leur position initiale et efface les traces."""
        self._anim_timer.stop()
        self._anim_queues.clear()
        self._anim_currents.clear()
        self._active_trails.clear()
        self._trails.clear()
        self._speed_factor = 1.0
        for robot in self._robots:
            robot["x"] = robot.get("init_x", robot["x"])
            robot["y"] = robot.get("init_y", robot["y"])
            robot["theta"] = robot.get("init_theta", robot["theta"])
        for zone in self._dynamic_zones:
            zone["active"] = zone.get("_init_active", True)
        self._bg_cache = None
        self.update()

    # --- Zones dynamiques -------------------------------------------------------

    def set_zone_active(self, zone_id: str, active: bool):
        """Active ou désactive une zone dynamique par son id."""
        for zone in self._dynamic_zones:
            if zone.get("id") == zone_id:
                zone["active"] = active
                self._bg_cache = None
                self.update()
                return

    # --- Animation helpers ------------------------------------------------------

    def is_robot_animating(self, robot_idx: int) -> bool:
        """Retourne True si le robot a des animations en cours ou en attente."""
        return (robot_idx in self._anim_currents or
                bool(self._anim_queues.get(robot_idx)))

    def set_anim_speed(self, factor: float):
        """Modifie le multiplicateur de vitesse d'animation (1.0 = normal)."""
        self._speed_factor = max(0.05, float(factor))

    # --- Zoom & Panoramique ---------------------------------------------------

    def set_zoom(self, zoom: float):
        """Applique un nouveau niveau de zoom centré sur le milieu du widget."""
        # Coordonnée table au centre du widget avant le zoom
        old_scale, old_ox, old_oy = self._compute_transform()
        center_x, center_y = self.width() / 2, self.height() / 2
        table_x = (center_x - old_ox) / old_scale
        table_y = (center_y - old_oy) / old_scale

        self._zoom = zoom

        # Recalculer le pan pour garder le centre fixe
        svg_w, svg_h = self._get_svg_size()
        if svg_w <= 0 or svg_h <= 0:
            return
        base_scale = min(self.width() / svg_w, self.height() / svg_h)
        new_scale = base_scale * self._zoom
        new_center_ox = (self.width() - svg_w * new_scale) / 2
        new_center_oy = (self.height() - svg_h * new_scale) / 2
        self._pan = QPointF(
            center_x - table_x * new_scale - new_center_ox,
            center_y - table_y * new_scale - new_center_oy,
        )
        self._bg_cache = None
        self.update()

    def resizeEvent(self, event):
        """Invalide le cache de fond lors d'un redimensionnement."""
        self._bg_cache = None
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        """Début du panoramique (clic gauche maintenu)."""
        from PySide6.QtCore import Qt
        if event.button() == Qt.MouseButton.LeftButton:
            self._panning = True
            self._pan_start = event.position()
            self._pan_at_start = QPointF(self._pan)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        """Déplacement pendant le panoramique."""
        if self._panning:
            delta = event.position() - self._pan_start
            self._pan = QPointF(
                self._pan_at_start.x() + delta.x(),
                self._pan_at_start.y() + delta.y(),
            )
            self._bg_cache = None
            self.update()

    def mouseReleaseEvent(self, event):
        """Fin du panoramique."""
        from PySide6.QtCore import Qt
        if event.button() == Qt.MouseButton.LeftButton:
            self._panning = False
            self.unsetCursor()

    def paintEvent(self, event):
        """
        Dessine la scène en deux passes :
        - Le fond (SVG + zones) est mis en cache dans un QPixmap et n'est
          recalculé que lorsque la vue ou les zones changent.
        - Traces et robots sont redessinés par-dessus à chaque frame.
        """
        if not self._renderer.isValid():
            return

        svg_w, svg_h = self._get_svg_size()
        if svg_w <= 0 or svg_h <= 0:
            return

        scale, offset_x, offset_y = self._compute_transform()

        # --- Passe 1 : construire le cache de fond si nécessaire ---
        if self._bg_cache is None or self._bg_cache.size() != self.size():
            self._bg_cache = QPixmap(self.size())
            self._bg_cache.fill(Qt.GlobalColor.transparent)
            bg_painter = QPainter(self._bg_cache)
            bg_painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            self._renderer.render(
                bg_painter,
                QRectF(offset_x, offset_y, svg_w * scale, svg_h * scale)
            )
            if self._grid_renderer.isValid():
                self._grid_renderer.render(
                    bg_painter,
                    QRectF(offset_x, offset_y, svg_w * scale, svg_h * scale)
                )
            if self._show_forbidden and self._forbidden_zones:
                self._draw_zones(bg_painter, self._forbidden_zones,
                                 QColor(255, 0, 0), scale, offset_x, offset_y)
            if self._show_dynamic and self._dynamic_zones:
                self._draw_zones(bg_painter, self._dynamic_zones,
                                 QColor(255, 165, 0), scale, offset_x, offset_y)
            bg_painter.end()

        # --- Passe 2 : coller le cache puis dessiner traces + robots ---
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.drawPixmap(0, 0, self._bg_cache)

        if self._trails or self._active_trails:
            self._draw_trails(painter, scale, offset_x, offset_y)

        if self._robots:
            self._draw_robots(painter, scale, offset_x, offset_y)

        if self._detections:
            self._draw_detections(painter, scale, offset_x, offset_y)

        painter.end()


class FlexDoubleSpinBox(QDoubleSpinBox):
    """
    QDoubleSpinBox acceptant indifféremment '.' et ',' comme séparateur décimal.
    La locale C est forcée pour que l'affichage utilise toujours le point.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLocale(QLocale(QLocale.Language.C))

    def validate(self, text: str, pos: int):
        return super().validate(text.replace(',', '.'), pos)

    def valueFromText(self, text: str) -> float:
        return super().valueFromText(text.replace(',', '.'))


class ManualControlWindow(QWidget):
    """Fenêtre de contrôle manuel des robots."""

    def __init__(self, table_widget: TableWidget, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Contrôle manuel")
        self.setWindowFlag(Qt.WindowType.Window)
        self.table_widget = table_widget
        self._fields: list[tuple[QDoubleSpinBox, QDoubleSpinBox, QDoubleSpinBox]] = []

        layout = QGridLayout(self)

        for i, robot in enumerate(table_widget._robots):
            row = i
            # Identifiant
            id_label = QLabel(f"<b>{robot['id']}</b>")
            color = robot.get("trail_color", ROBOT_TRAIL_COLORS[0])
            id_label.setStyleSheet(f"color: {color.name()};")
            layout.addWidget(id_label, row, 0)

            # X
            layout.addWidget(QLabel("X :"), row, 1)
            x_spin = QDoubleSpinBox()
            x_spin.setRange(0, 5000)
            x_spin.setDecimals(0)
            x_spin.setValue(robot["x"])
            layout.addWidget(x_spin, row, 2)

            # Y
            layout.addWidget(QLabel("Y :"), row, 3)
            y_spin = QDoubleSpinBox()
            y_spin.setRange(0, 5000)
            y_spin.setDecimals(0)
            y_spin.setValue(robot["y"])
            layout.addWidget(y_spin, row, 4)

            # Theta
            layout.addWidget(QLabel("θ :"), row, 5)
            theta_spin = FlexDoubleSpinBox()
            theta_spin.setRange(-6.29, 6.29)
            theta_spin.setDecimals(2)
            theta_spin.setSingleStep(0.1)
            theta_spin.setValue(round(robot["theta"], 2))
            layout.addWidget(theta_spin, row, 6)

            # Bouton Déplacer
            btn = QPushButton("Déplacer")
            btn.clicked.connect(lambda checked, idx=i: self._on_move(idx))
            layout.addWidget(btn, row, 7)

            self._fields.append((x_spin, y_spin, theta_spin))

    def _on_move(self, robot_idx: int):
        """Lance l'animation de déplacement pour le robot donné."""
        x_spin, y_spin, theta_spin = self._fields[robot_idx]
        robot = self.table_widget._robots[robot_idx]
        self.table_widget.animate_robot_move(
            robot["id"],
            x_spin.value(),
            y_spin.value(),
            theta_spin.value(),
            robot.get("trail_color", ROBOT_TRAIL_COLORS[robot_idx % len(ROBOT_TRAIL_COLORS)]),
        )


class StrategyWindow(QWidget):
    """Fenêtre de chargement et lecture des stratégies."""

    def __init__(self, table_widget: TableWidget, year: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stratégies")
        self.setWindowFlag(Qt.WindowType.Window)
        self.setMinimumSize(640, 420)

        self._table_widget = table_widget
        self._year = year
        self._strategies: dict[str, list[dict]] = {}
        self._cursors: dict[str, int] = {}
        self._wait_until: dict[str, float] = {}  # robot_id → time.monotonic()

        # Lire les couleurs depuis table.json
        json_path = os.path.join(SIMULATION_DIR, year, "table.json")
        self._color_options: list[tuple[str, str]] = []  # (label, "0"|"3000")
        if os.path.isfile(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                tdata = json.load(f)
            self._color_options = [
                (tdata.get("color0", "couleur 0"), "0"),
                (tdata.get("color3000", "couleur 3000"), "3000"),
            ]

        layout = QVBoxLayout(self)

        # --- Ligne 1 : couleur + robots ---
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Couleur :"))
        self.color_combo = QComboBox()
        for label, key in self._color_options:
            self.color_combo.addItem(label, key)
        row1.addWidget(self.color_combo)
        row1.addSpacing(16)

        self._robot_checks: dict[str, QCheckBox] = {}
        for robot in table_widget._robots:
            cb = QCheckBox(robot["id"])
            c = robot.get("trail_color", ROBOT_TRAIL_COLORS[0])
            cb.setStyleSheet(f"color: {c.name()}; font-weight: bold;")
            cb.setChecked(True)
            self._robot_checks[robot["id"]] = cb
            row1.addWidget(cb)

        btn_all = QPushButton("Tous")
        btn_all.clicked.connect(self._select_all)
        row1.addWidget(btn_all)
        row1.addStretch()
        layout.addLayout(row1)

        # --- Ligne 2 : boutons d'action ---
        row2 = QHBoxLayout()
        self.btn_load = QPushButton("Charger")
        self.btn_load.clicked.connect(self._on_load)
        row2.addWidget(self.btn_load)

        self.btn_next = QPushButton("Suivant")
        self.btn_next.clicked.connect(self._on_next)
        self.btn_next.setEnabled(False)
        row2.addWidget(self.btn_next)

        self.btn_play = QPushButton("Lecture")
        self.btn_play.clicked.connect(self._on_play)
        self.btn_play.setEnabled(False)
        row2.addWidget(self.btn_play)

        self.btn_pause = QPushButton("Pause")
        self.btn_pause.clicked.connect(self._on_pause)
        self.btn_pause.setEnabled(False)
        row2.addWidget(self.btn_pause)

        row2.addStretch()
        layout.addLayout(row2)

        # --- Zone de log scrollable ---
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        font = QFont("Courier New", 9)
        self._log.setFont(font)
        layout.addWidget(self._log, stretch=1)

        # Timer de lecture automatique
        self._play_timer = QTimer(self)
        self._play_timer.setInterval(30)  # vérifie toutes les 30 ms
        self._play_timer.timeout.connect(self._play_tick)

    # --- Sélection robots -------------------------------------------------------

    def _select_all(self):
        all_checked = all(cb.isChecked() for cb in self._robot_checks.values())
        for cb in self._robot_checks.values():
            cb.setChecked(not all_checked)

    # --- Chargement stratégie ---------------------------------------------------

    def _on_load(self):
        self._play_timer.stop()
        self._strategies.clear()
        self._cursors.clear()
        self._wait_until.clear()
        self._match_start_time = None
        self._log.clear()

        color_key = self.color_combo.currentData() or "0"

        for robot_id, cb in self._robot_checks.items():
            if not cb.isChecked():
                continue
            filename = f"strategy-{robot_id}-{color_key}.json"
            path = os.path.join(SIMULATION_DIR, self._year, filename)
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    instructions = json.load(f)
                self._strategies[robot_id] = instructions
                self._cursors[robot_id] = 0
                self._log_text(
                    f"✓ {filename}  ({len(instructions)} instructions)",
                    QColor(100, 210, 100)
                )
            else:
                self._log_text(f"✗ Introuvable : {filename}", QColor(220, 80, 80))

        has = bool(self._strategies)
        self.btn_next.setEnabled(has)
        self.btn_play.setEnabled(has)
        self.btn_pause.setEnabled(False)

    # --- Exécution --------------------------------------------------------------

    def _on_next(self):
        """Exécute la prochaine instruction pour chaque robot coché."""
        for robot_id in list(self._strategies.keys()):
            if self._robot_checks.get(robot_id, QCheckBox()).isChecked():
                self._dispatch_next(robot_id)

    def _dispatch_next(self, robot_id: str):
        """Envoie la prochaine instruction au robot et avance son curseur."""
        instructions = self._strategies.get(robot_id, [])
        cursor = self._cursors.get(robot_id, 0)
        if cursor >= len(instructions):
            return
        instr = instructions[cursor]
        self._cursors[robot_id] = cursor + 1
        self._execute(robot_id, instr)

    def _execute(self, robot_id: str, instr: dict):
        """Analyse et exécute une instruction pour un robot donné."""
        task = instr.get("task", "")
        command = instr.get("command", "")
        position = instr.get("position", {})

        robot = next(
            (r for r in self._table_widget._robots if r["id"] == robot_id), None
        )
        color = robot.get("trail_color", QColor(200, 200, 200)) if robot else QColor(200, 200, 200)

        # Log dans la couleur du robot
        self._log_text(f"[{robot_id}]  {task}  :  {command}", color)

        # --- Commandes spéciales ---
        if command.startswith("delete-zone#"):
            zone_id = command.split("#", 1)[1]
            self._table_widget.set_zone_active(zone_id, False)

        elif command.startswith("add-zone#"):
            zone_id = command.split("#", 1)[1]
            self._table_widget.set_zone_active(zone_id, True)

        elif command.startswith("speed#"):
            try:
                pct = float(command.split("#", 1)[1])
                self._table_widget.set_anim_speed(pct / 100.0)
            except ValueError:
                pass

        elif command.startswith("wait#"):
            try:
                ms = float(command.split("#", 1)[1])
                self._wait_until[robot_id] = time.monotonic() + ms / 1000.0
            except ValueError:
                pass

        elif command.startswith("wait-chrono#"):
            try:
                target_seconds = float(command.split("#", 1)[1])
                start = getattr(self, '_match_start_time', None) or time.monotonic()
                self._wait_until[robot_id] = start + target_seconds
            except ValueError:
                pass

        # --- Orbital turn : animation en arc de cercle ---
        if command.startswith("orbital-turn#") and robot is not None:
            try:
                parts = command.split("#", 1)[1].split(";")
                degrees = float(parts[0])
                forward = int(parts[1]) == 1
                on_right_wheel = int(parts[2]) == 1
                self._table_widget.animate_robot_orbital(robot_id, degrees, forward, on_right_wheel, color)
            except (ValueError, IndexError):
                pass
            return

        # --- Déplacement du robot (toujours, vers la position de l'instruction) ---
        if robot is not None and position:
            px = position.get("x", robot["x"])
            py = position.get("y", robot["y"])
            pt = position.get("theta", robot["theta"])
            self._table_widget.animate_robot_move(robot_id, px, py, pt, color)

    # --- Lecture automatique ----------------------------------------------------

    def _on_play(self):
        self.btn_play.setEnabled(False)
        self.btn_next.setEnabled(False)
        self.btn_pause.setEnabled(True)
        if not hasattr(self, '_match_start_time') or self._match_start_time is None:
            self._match_start_time = time.monotonic()
        self._play_timer.start()

    def _on_pause(self):
        self._play_timer.stop()
        self.btn_play.setEnabled(True)
        self.btn_next.setEnabled(True)
        self.btn_pause.setEnabled(False)

    def _play_tick(self):
        """
        Timer de lecture : dispatche la prochaine instruction d'un robot
        dès qu'il a fini d'animer et que son éventuel délai d'attente est écoulé.
        """
        now = time.monotonic()
        all_done = True

        for robot_id, instructions in self._strategies.items():
            if not self._robot_checks.get(robot_id, QCheckBox()).isChecked():
                continue

            cursor = self._cursors.get(robot_id, 0)
            if cursor >= len(instructions):
                continue  # ce robot a terminé sa stratégie
            all_done = False

            # Encore en attente temporelle (wait / wait-chrono) ?
            if now < self._wait_until.get(robot_id, 0.0):
                continue

            # Encore en cours d'animation ?
            robot_idx = next(
                (i for i, r in enumerate(self._table_widget._robots) if r["id"] == robot_id),
                None
            )
            if robot_idx is not None and self._table_widget.is_robot_animating(robot_idx):
                continue

            # Prêt : dispatcherl'instruction suivante
            self._dispatch_next(robot_id)

        if all_done:
            self._on_pause()
            self._log_text("■ Stratégie terminée.", QColor(100, 220, 100))

    # --- Log --------------------------------------------------------------------

    def _log_text(self, message: str, color: QColor):
        """Ajoute un message coloré dans la zone de log et scroll vers le bas."""
        escaped = html_module.escape(message)
        self._log.append(f'<span style="color:{color.name()};">{escaped}</span>')
        sb = self._log.verticalScrollBar()
        sb.setValue(sb.maximum())


class LogSocketWorker(QObject):
    """
    Worker tournant dans un QThread séparé.
    Se connecte au serveur de logs, envoie "logListener" et lit en continu.
    """
    message_received = Signal(str)
    connection_status = Signal(str, bool)  # message, is_error

    def __init__(self, host: str, port: int):
        super().__init__()
        self._host = host
        self._port = port
        self._running = False
        self._sock = None

    def start_connection(self):
        self._running = True
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(5.0)
            self._sock.connect((self._host, self._port))
            self._sock.sendall(b"logListener")
            # Lire la réponse initiale du serveur
            self._sock.settimeout(2.0)
            try:
                resp = self._sock.recv(1024).decode(errors='replace').strip()
                if resp:
                    self.connection_status.emit(resp, False)
            except socket.timeout:
                pass
            self._sock.settimeout(1.0)
            buffer = ""
            while self._running:
                try:
                    data = self._sock.recv(4096).decode(errors='replace')
                    if not data:
                        break
                    buffer += data
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if line:
                            self.message_received.emit(line)
                except socket.timeout:
                    continue
                except OSError:
                    break
        except Exception as e:
            self.connection_status.emit(str(e), True)
        finally:
            if self._sock:
                try:
                    self._sock.close()
                except OSError:
                    pass
            if self._running:
                self.connection_status.emit("Déconnecté du serveur", True)

    def stop(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass


class RealtimeLogWindow(QWidget):
    """Fenêtre d'affichage des logs en temps réel depuis le serveur."""

    def __init__(self, host: str, port: int, robots: list[dict], table_widget: "TableWidget", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Logs temps réel")
        self.setWindowFlag(Qt.WindowType.Window)
        self.setMinimumSize(900, 500)

        # Mapping robot_id → QColor
        self._robot_colors: dict[str, QColor] = {}
        for robot in robots:
            self._robot_colors[robot["id"]] = robot.get("trail_color", ROBOT_TRAIL_COLORS[0])

        self._table_widget = table_widget
        self._worker: LogSocketWorker | None = None
        self._thread: QThread | None = None

        layout = QVBoxLayout(self)

        # --- En-têtes robots colorés ---
        header = QHBoxLayout()
        for robot_id, color in self._robot_colors.items():
            lbl = QLabel(f"● {robot_id}")
            lbl.setStyleSheet(f"color: {color.name()}; font-weight: bold;")
            header.addWidget(lbl)
        header.addStretch()
        layout.addLayout(header)

        # --- Zone de log ---
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Courier New", 9))
        layout.addWidget(self._log, stretch=1)

        self._start_connection(host, port)

    def _start_connection(self, host: str, port: int):
        self._thread = QThread()
        self._worker = LogSocketWorker(host, port)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.start_connection)
        self._worker.message_received.connect(self._on_message)
        self._worker.connection_status.connect(self._on_status)
        self._thread.start()

    def _parse_line(self, line: str) -> tuple[str, str, str, str] | None:
        """
        Parse une ligne de log au format "timestamp - who - level - message".
        Retourne (timestamp, who, level, message) ou None si le format ne correspond pas.
        """
        parts = line.split(' - ', 3)
        if len(parts) == 4:
            return parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
        return None

    def _color_for_robot(self, robot_id: str) -> QColor:
        if robot_id in self._robot_colors:
            return self._robot_colors[robot_id]
        for rid, color in self._robot_colors.items():
            if rid in robot_id:
                return color
        return QColor(200, 200, 200)

    def _on_message(self, line: str):
        parsed = self._parse_line(line)
        if parsed is None:
            self._log_text(line, QColor(200, 200, 200))
            return

        _timestamp, who, level, message = parsed

        # Filtrer les DEBUG (mais traiter quand même les positions et détections)
        if level == "DEBUG":
            if message.startswith("Position :"):
                self._handle_position(who, message)
            elif "detected an obstacle at position" in message or message.startswith("Lidar detection:"):
                self._handle_detection(who, message)
            return

        # Déplacement du robot si c'est une ligne de position
        if message.startswith("Position :"):
            self._handle_position(who, message)
            return

        self._log_text(line, self._color_for_robot(who))

    def _handle_position(self, robot_id: str, message: str):
        """Parse la position et anime le robot correspondant sur la table."""
        try:
            dict_str = message[len("Position :"):].strip()
            pos = ast.literal_eval(dict_str)
            x = float(pos["x"])
            y = float(pos["y"])
            theta = float(pos["theta"])
            color = self._color_for_robot(robot_id)
            self._table_widget.animate_robot_move(robot_id, x, y, theta, color)
        except (ValueError, KeyError, SyntaxError):
            pass

    def _handle_detection(self, robot_id: str, message: str):
        """Parse une détection d'obstacle et l'affiche sur la table."""
        color = self._color_for_robot(robot_id)
        # Format 1 (detection_manager) : "Sensor X detected an obstacle at position (x,y)"
        m = re.search(r'at position \((-?\d+),(-?\d+)\)', message)
        if m:
            self._table_widget.add_detection(float(m.group(1)), float(m.group(2)), color)
            return
        # Format 2 (lidar) : "Lidar detection: Position(x=X, y=Y, theta=...)"
        m = re.search(r'Lidar detection: Position\(x=(-?\d+), y=(-?\d+)', message)
        if m:
            self._table_widget.add_detection(float(m.group(1)), float(m.group(2)), color)

    def _on_status(self, message: str, is_error: bool):
        color = QColor(220, 80, 80) if is_error else QColor(100, 210, 100)
        self._log_text(f"[{message}]", color)

    def _log_text(self, message: str, color: QColor):
        escaped = html_module.escape(message)
        self._log.append(f'<span style="color:{color.name()};">{escaped}</span>')
        sb = self._log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def closeEvent(self, event):
        if self._worker:
            self._worker.stop()
        if self._thread:
            self._thread.quit()
            self._thread.wait(2000)
        super().closeEvent(event)


class LogFileWorker(QObject):
    """Worker qui lit un fichier de log et émet les lignes en respectant les timestamps."""
    message_received = Signal(str)
    playback_finished = Signal()

    def __init__(self, filepath: str, speed: float = 1.0):
        super().__init__()
        self._filepath = filepath
        self._speed = speed
        self._running = False
        self._paused = False

    def set_speed(self, speed: float):
        self._speed = max(0.1, speed)

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self._running = False
        self._paused = False

    def start_playback(self):
        self._running = True
        self._paused = False
        prev_ts = None
        skip_until_match = False

        try:
            with open(self._filepath, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if not self._running:
                        break
                    line = line.strip()
                    if not line:
                        continue

                    # Skip entre "Attente lancement match" et "Match lancé"
                    if "Attente lancement match" in line:
                        skip_until_match = True
                    if skip_until_match:
                        if "Match lancé" in line:
                            skip_until_match = False
                            prev_ts = self._parse_timestamp(line)
                        self.message_received.emit(line)
                        continue

                    # Respecter les timestamps (plafonné à 0.5s réel pour skip les temps morts)
                    ts = self._parse_timestamp(line)
                    if ts is not None and prev_ts is not None:
                        delay = min((ts - prev_ts) / self._speed, 0.5)
                        if delay > 0:
                            deadline = time.monotonic() + delay
                            while time.monotonic() < deadline and self._running:
                                time.sleep(0.005)
                    if ts is not None:
                        prev_ts = ts

                    # Attente si en pause
                    while self._paused and self._running:
                        time.sleep(0.05)

                    if self._running:
                        self.message_received.emit(line)
        except Exception:
            pass
        finally:
            self.playback_finished.emit()

    @staticmethod
    def _parse_timestamp(line: str) -> float | None:
        parts = line.split(' - ', 1)
        if len(parts) < 2:
            return None
        try:
            return datetime.strptime(parts[0].strip(), "%Y-%m-%d %H:%M:%S,%f").timestamp()
        except ValueError:
            return None


class LogReplayWindow(QWidget):
    """Fenêtre de relecture de logs depuis un fichier."""

    def __init__(self, robots: list[dict], table_widget: "TableWidget", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Relecture de logs")
        self.setWindowFlag(Qt.WindowType.Window)
        self.setMinimumSize(900, 500)

        self._robot_colors: dict[str, QColor] = {}
        for robot in robots:
            self._robot_colors[robot["id"]] = robot.get("trail_color", ROBOT_TRAIL_COLORS[0])

        self._table_widget = table_widget
        self._worker: LogFileWorker | None = None
        self._thread: QThread | None = None

        layout = QVBoxLayout(self)

        # En-têtes robots colorés
        header = QHBoxLayout()
        for robot_id, color in self._robot_colors.items():
            lbl = QLabel(f"● {robot_id}")
            lbl.setStyleSheet(f"color: {color.name()}; font-weight: bold;")
            header.addWidget(lbl)
        header.addStretch()
        layout.addLayout(header)

        # Contrôles
        controls = QHBoxLayout()
        self._btn_open = QPushButton("Ouvrir un log")
        self._btn_open.clicked.connect(self._on_open)
        controls.addWidget(self._btn_open)

        self._btn_play = QPushButton("Play")
        self._btn_play.clicked.connect(self._on_play)
        self._btn_play.setEnabled(False)
        controls.addWidget(self._btn_play)

        self._btn_pause = QPushButton("Pause")
        self._btn_pause.clicked.connect(self._on_pause)
        self._btn_pause.setEnabled(False)
        controls.addWidget(self._btn_pause)

        self._btn_stop = QPushButton("Stop")
        self._btn_stop.clicked.connect(self._on_stop)
        self._btn_stop.setEnabled(False)
        controls.addWidget(self._btn_stop)

        controls.addWidget(QLabel("Vitesse:"))
        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setMinimum(1)
        self._speed_slider.setMaximum(100)
        self._speed_slider.setValue(10)
        self._speed_slider.setFixedWidth(120)
        self._speed_slider.valueChanged.connect(self._on_speed_changed)
        controls.addWidget(self._speed_slider)
        self._speed_label = QLabel("x1.0")
        controls.addWidget(self._speed_label)

        controls.addStretch()
        layout.addLayout(controls)

        # Zone de log
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Courier New", 9))
        layout.addWidget(self._log, stretch=1)

        self._filepath: str | None = None

    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Ouvrir un fichier de log", "", "Log files (*.log);;All files (*)")
        if path:
            self._on_stop()
            self._filepath = path
            self._log.clear()
            self._log_text(f"Fichier chargé : {path}", QColor(100, 210, 100))
            self._btn_play.setEnabled(True)

    def _on_play(self):
        if self._worker is not None and self._thread is not None and self._thread.isRunning():
            # Resume from pause
            self._worker.resume()
        else:
            if self._filepath is None:
                return
            self._log.clear()
            self._thread = QThread()
            self._worker = LogFileWorker(self._filepath, self._current_speed())
            self._worker.moveToThread(self._thread)
            self._thread.started.connect(self._worker.start_playback)
            self._worker.message_received.connect(self._on_message)
            self._worker.playback_finished.connect(self._on_finished)
            self._thread.start()
        self._btn_play.setEnabled(False)
        self._btn_pause.setEnabled(True)
        self._btn_stop.setEnabled(True)

    def _on_pause(self):
        if self._worker:
            self._worker.pause()
        self._btn_play.setEnabled(True)
        self._btn_pause.setEnabled(False)

    def _on_stop(self):
        if self._worker:
            self._worker.stop()
        if self._thread:
            self._thread.quit()
            self._thread.wait(2000)
            self._thread = None
            self._worker = None
        self._btn_play.setEnabled(self._filepath is not None)
        self._btn_pause.setEnabled(False)
        self._btn_stop.setEnabled(False)

    def _on_finished(self):
        self._log_text("Relecture terminée.", QColor(100, 210, 100))
        self._btn_play.setEnabled(self._filepath is not None)
        self._btn_pause.setEnabled(False)
        self._btn_stop.setEnabled(False)

    def _current_speed(self) -> float:
        return self._speed_slider.value() / 10.0

    def _on_speed_changed(self, value: int):
        speed = value / 10.0
        self._speed_label.setText(f"x{speed:.1f}")
        if self._worker:
            self._worker.set_speed(speed)

    def _parse_line(self, line: str) -> tuple[str, str, str, str] | None:
        parts = line.split(' - ', 3)
        if len(parts) == 4:
            return parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
        return None

    def _color_for_robot(self, robot_id: str) -> QColor:
        if robot_id in self._robot_colors:
            return self._robot_colors[robot_id]
        for rid, color in self._robot_colors.items():
            if rid in robot_id:
                return color
        return QColor(200, 200, 200)

    def _on_message(self, line: str):
        parsed = self._parse_line(line)
        if parsed is None:
            self._log_text(line, QColor(200, 200, 200))
            return

        _timestamp, who, level, message = parsed

        if level == "DEBUG":
            if message.startswith("Position :"):
                self._handle_position(who, message)
            elif "detected an obstacle at position" in message or message.startswith("Lidar detection:"):
                self._handle_detection(who, message)
            return

        if message.startswith("Position :"):
            self._handle_position(who, message)
            return

        self._log_text(line, self._color_for_robot(who))

    def _handle_position(self, robot_id: str, message: str):
        try:
            dict_str = message[len("Position :"):].strip()
            pos = ast.literal_eval(dict_str)
            x = float(pos["x"])
            y = float(pos["y"])
            theta = float(pos["theta"])
            color = self._color_for_robot(robot_id)
            self._table_widget.animate_robot_move(robot_id, x, y, theta, color)
        except (ValueError, KeyError, SyntaxError):
            pass

    def _handle_detection(self, robot_id: str, message: str):
        color = self._color_for_robot(robot_id)
        m = re.search(r'at position \((-?\d+),(-?\d+)\)', message)
        if m:
            self._table_widget.add_detection(float(m.group(1)), float(m.group(2)), color)
            return
        m = re.search(r'Lidar detection: Position\(x=(-?\d+), y=(-?\d+)', message)
        if m:
            self._table_widget.add_detection(float(m.group(1)), float(m.group(2)), color)

    def _log_text(self, message: str, color: QColor):
        escaped = html_module.escape(message)
        self._log.append(f'<span style="color:{color.name()};">{escaped}</span>')
        sb = self._log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def closeEvent(self, event):
        self._on_stop()
        super().closeEvent(event)


class SimulatorWindow(QMainWindow):
    """Fenêtre principale du simulateur."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulateur Robot 2D")

        # --- Config simulateur ---
        config_path = os.path.join(SIMULATION_DIR, "config.json")
        self._sim_config: dict = {}
        if os.path.isfile(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self._sim_config = json.load(f)

        # --- Widget central ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 10, 20, 20)

        # --- Barre de contrôle ---
        control_layout = QHBoxLayout()
        main_layout.addLayout(control_layout)

        label = QLabel("Année :")
        control_layout.addWidget(label)

        self.year_combo = QComboBox()
        self.available_years = get_available_years()
        self.year_combo.addItems(self.available_years)
        if self.available_years:
            self.year_combo.setCurrentIndex(len(self.available_years) - 1)
        self.year_combo.currentTextChanged.connect(self._on_year_changed)
        control_layout.addWidget(self.year_combo)

        # Bouton toggle zones interdites (rouge)
        self.btn_forbidden = QPushButton("Zones interdites")
        self.btn_forbidden.setCheckable(True)
        self.btn_forbidden.setChecked(False)
        self.btn_forbidden.toggled.connect(self._on_toggle_forbidden)
        control_layout.addWidget(self.btn_forbidden)

        # Bouton toggle zones dynamiques (orange)
        self.btn_dynamic = QPushButton("Zones dynamiques")
        self.btn_dynamic.setCheckable(True)
        self.btn_dynamic.setChecked(False)
        self.btn_dynamic.toggled.connect(self._on_toggle_dynamic)
        control_layout.addWidget(self.btn_dynamic)

        # Sélecteur de zoom
        control_layout.addWidget(QLabel("Zoom :"))
        self.zoom_combo = QComboBox()
        self._zoom_levels = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0]
        for level in self._zoom_levels:
            self.zoom_combo.addItem(f"{int(level * 100)} %", level)
        self.zoom_combo.setCurrentIndex(self._zoom_levels.index(1.0))
        self.zoom_combo.currentIndexChanged.connect(self._on_zoom_changed)
        control_layout.addWidget(self.zoom_combo)

        # Bouton contrôle manuel
        self.btn_manual = QPushButton("Manuel")
        self.btn_manual.clicked.connect(self._on_manual_click)
        control_layout.addWidget(self.btn_manual)

        # Bouton stratégies
        self.btn_strategy = QPushButton("Stratégies")
        self.btn_strategy.clicked.connect(self._on_strategy_click)
        control_layout.addWidget(self.btn_strategy)

        # Bouton temps réel
        self.btn_realtime = QPushButton("Temps réel")
        self.btn_realtime.clicked.connect(self._on_realtime_click)
        control_layout.addWidget(self.btn_realtime)

        # Bouton relecture logs
        self.btn_replay = QPushButton("Relecture logs")
        self.btn_replay.clicked.connect(self._on_replay_click)
        control_layout.addWidget(self.btn_replay)

        # Bouton reset
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.clicked.connect(self._on_reset_click)
        control_layout.addWidget(self.btn_reset)

        control_layout.addStretch()

        # --- Affichage de la table (SVG) ---
        self.table_widget = TableWidget()
        main_layout.addWidget(self.table_widget, stretch=1)

        self._manual_window: ManualControlWindow | None = None
        self._strategy_window: StrategyWindow | None = None
        self._realtime_window: RealtimeLogWindow | None = None
        self._replay_window: LogReplayWindow | None = None
        self._current_year: str = ""

        # Charger l'année par défaut
        if self.available_years:
            self._load_table(self.available_years[-1])

    def _on_year_changed(self, year: str):
        """Appelé quand l'utilisateur change l'année dans le combo."""
        self._load_table(year)

    def _on_toggle_forbidden(self, checked: bool):
        self.table_widget.set_show_forbidden(checked)

    def _on_toggle_dynamic(self, checked: bool):
        self.table_widget.set_show_dynamic(checked)

    def _on_zoom_changed(self, index: int):
        if 0 <= index < len(self._zoom_levels):
            self.table_widget.set_zoom(self._zoom_levels[index])

    def _on_manual_click(self):
        """Ouvre (ou recrée) la fenêtre de contrôle manuel."""
        if self._manual_window is not None:
            self._manual_window.close()
        self._manual_window = ManualControlWindow(self.table_widget, self)
        self._manual_window.show()

    def _on_strategy_click(self):
        """Ouvre (ou recrée) la fenêtre de stratégies."""
        if self._strategy_window is not None:
            self._strategy_window.close()
        self._strategy_window = StrategyWindow(self.table_widget, self._current_year, self)
        self._strategy_window.show()

    def _on_realtime_click(self):
        """Ouvre (ou recrée) la fenêtre de logs temps réel."""
        if self._realtime_window is not None:
            self._realtime_window.close()
        com = self._sim_config.get("comSocket", {})
        host = com.get("host", "localhost")
        port = com.get("port", 4269)
        self._realtime_window = RealtimeLogWindow(host, port, self.table_widget._robots, self.table_widget, self)
        self._realtime_window.show()

    def _on_replay_click(self):
        """Ouvre (ou recrée) la fenêtre de relecture de logs."""
        if self._replay_window is not None:
            self._replay_window.close()
        self._replay_window = LogReplayWindow(self.table_widget._robots, self.table_widget, self)
        self._replay_window.show()

    def _on_reset_click(self):
        """Ferme les sous-fenêtres, efface les traces et remet les robots à l'origine."""
        if self._manual_window is not None:
            self._manual_window.close()
            self._manual_window = None
        if self._strategy_window is not None:
            self._strategy_window.close()
            self._strategy_window = None
        if self._realtime_window is not None:
            self._realtime_window.close()
            self._realtime_window = None
        if self._replay_window is not None:
            self._replay_window.close()
            self._replay_window = None
        self.table_widget.reset()

    def _load_table(self, year: str):
        """Charge et affiche le SVG de la table pour l'année donnée."""
        # Fermer les fenêtres annexes
        if self._manual_window is not None:
            self._manual_window.close()
            self._manual_window = None
        if self._strategy_window is not None:
            self._strategy_window.close()
            self._strategy_window = None
        if self._realtime_window is not None:
            self._realtime_window.close()
            self._realtime_window = None
        self._current_year = year
        svg_path = get_table_svg_path(year)
        if os.path.isfile(svg_path):
            table_size = get_table_size(year)
            self.table_widget.load(svg_path, table_size)
            # Réinitialiser le zoom à 100 %
            self.zoom_combo.setCurrentIndex(self._zoom_levels.index(1.0))
            # Charger les zones
            forbidden, dynamic = load_table_zones(year)
            self.table_widget.set_zones(forbidden, dynamic)
            # Charger les robots
            robots = load_robots(year)
            self.table_widget.set_robots(robots)
            self.setWindowTitle(f"Simulateur Robot 2D — Table {year}")


def main():
    app = QApplication(sys.argv)

    window = SimulatorWindow()
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

