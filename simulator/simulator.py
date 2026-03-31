"""
Simulateur 2D pour robot - Affichage de la table de jeu.
Utilise PySide6 pour le rendu SVG natif.
"""

import html as html_module
import json
import math
import os
import sys
import time
from datetime import datetime

from PySide6.QtCore import QRectF, QPointF, QTimer, QElapsedTimer, Qt, QLocale
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QPixmap, QFont
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QComboBox, QLabel, QPushButton,
    QGridLayout, QDoubleSpinBox, QCheckBox, QTextEdit,
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
        self._active_trail: tuple | None = None  # trace du déplacement en cours

        # Animation
        self._anim_queue: list[dict] = []
        self._anim_current: dict | None = None
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._anim_tick)
        # Horloge globale démarrée une fois — jamais remise à zéro
        self._global_clock = QElapsedTimer()
        self._global_clock.start()

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
        self._active_trail = None
        self._anim_queue.clear()
        self._anim_current = None
        self._anim_timer.stop()
        self.update()

    def set_zones(self, forbidden: list, dynamic: list):
        """Définit les zones interdites et dynamiques à dessiner."""
        self._forbidden_zones = forbidden
        self._dynamic_zones = dynamic
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

        for zone in zones:
            if not zone.get("active", True):
                continue

            forme = zone.get("forme", "")
            if forme == "polygone":
                points = zone.get("points", [])
                if len(points) < 3:
                    continue
                polygon = QPolygonF([
                    self._to_screen(p["x"], p["y"], scale, offset_x, offset_y)
                    for p in points
                ])
                painter.drawPolygon(polygon)

            elif forme == "cercle":
                centre = zone.get("centre", {})
                rayon = zone.get("rayon", 0)
                center_pt = self._to_screen(
                    centre.get("x", 0), centre.get("y", 0),
                    scale, offset_x, offset_y
                )
                r_scaled = rayon * scale
                painter.drawEllipse(center_pt, r_scaled, r_scaled)

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
            painter.rotate(math.degrees(robot["theta"]))  # sens inversé par le swap d'axes
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
        all_trails = list(self._trails)
        if self._active_trail is not None:
            all_trails.append(self._active_trail)
        for x1, y1, x2, y2, color in all_trails:
            p1 = self._to_screen(x1, y1, scale, offset_x, offset_y)
            p2 = self._to_screen(x2, y2, scale, offset_x, offset_y)
            painter.setPen(QPen(color, 2))
            painter.drawLine(p1, p2)

    # --- Animation -------------------------------------------------------------

    def animate_robot_move(self, robot_id: str, target_x: float, target_y: float,
                           target_theta: float, trail_color: QColor):
        """
        Lance l'animation d'un robot : rotation vers la cible, déplacement,
        puis rotation vers l'angle final.
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

        # Rotation vers l'angle final
        self._anim_queue.append({
            "type": "rotate",
            "robot_idx": robot_idx,
            "to_theta": target_theta,
        })

        if distance > 1:
            # Déplacement en ligne droite
            self._anim_queue.append({
                "type": "move",
                "robot_idx": robot_idx,
                "to_x": target_x,
                "to_y": target_y,
                "trail_color": QColor(trail_color),
            })

        # Démarrer si aucune animation en cours
        if not self._anim_timer.isActive():
            self._start_next_anim()

    def _start_next_anim(self):
        """Démarre la prochaine étape d'animation de la file."""
        if not self._anim_queue:
            self._anim_current = None
            self._anim_timer.stop()
            return

        step = self._anim_queue.pop(0)
        robot = self._robots[step["robot_idx"]]

        if step["type"] == "rotate":
            from_theta = robot["theta"]
            diff = normalize_angle(step["to_theta"] - from_theta)
            if abs(diff) < 0.01:
                # Rotation négligeable, passer à l'étape suivante
                self._start_next_anim()
                return
            self._anim_current = {
                "type": "rotate",
                "robot_idx": step["robot_idx"],
                "from_theta": from_theta,
                "to_theta": from_theta + diff,
                "duration": abs(diff) / ANIM_ROTATION_SPEED,
                "start_time": self._global_clock.elapsed(),
            }

        elif step["type"] == "move":
            from_x, from_y = robot["x"], robot["y"]
            to_x, to_y = step["to_x"], step["to_y"]
            dist = math.sqrt((to_x - from_x) ** 2 + (to_y - from_y) ** 2)
            self._anim_current = {
                "type": "move",
                "robot_idx": step["robot_idx"],
                "from_x": from_x, "from_y": from_y,
                "to_x": to_x, "to_y": to_y,
                "duration": max(dist / (ANIM_MOVE_SPEED * self._speed_factor), 0.05),
                "start_time": self._global_clock.elapsed(),
                "trail_color": step.get("trail_color"),
            }

        self._anim_timer.start(ANIM_INTERVAL_MS)

    def _anim_tick(self):
        """Appelé à chaque tick du timer d'animation."""
        if self._anim_current is None:
            self._anim_timer.stop()
            return

        anim = self._anim_current
        # Temps absolu écoulé depuis le début de cette étape — pas d'accumulation d'erreur
        elapsed = (self._global_clock.elapsed() - anim["start_time"]) / 1000.0
        t = min(elapsed / anim["duration"], 1.0)
        robot = self._robots[anim["robot_idx"]]

        if anim["type"] == "rotate":
            robot["theta"] = anim["from_theta"] + (anim["to_theta"] - anim["from_theta"]) * t

        elif anim["type"] == "move":
            robot["x"] = anim["from_x"] + (anim["to_x"] - anim["from_x"]) * t
            robot["y"] = anim["from_y"] + (anim["to_y"] - anim["from_y"]) * t
            # Trace en cours : un seul segment grandissant (pas de micro-segments)
            if anim.get("trail_color"):
                self._active_trail = (
                    anim["from_x"], anim["from_y"],
                    robot["x"], robot["y"],
                    anim["trail_color"],
                )

        self.update()

        if t >= 1.0:
            # Finaliser la trace
            if anim["type"] == "move" and anim.get("trail_color"):
                self._trails.append((
                    anim["from_x"], anim["from_y"],
                    anim["to_x"], anim["to_y"],
                    anim["trail_color"],
                ))
                self._active_trail = None
            self._start_next_anim()

    def reset(self):
        """Remet les robots à leur position initiale et efface les traces."""
        self._anim_timer.stop()
        self._anim_queue.clear()
        self._anim_current = None
        self._active_trail = None
        self._trails.clear()
        self._speed_factor = 1.0
        for robot in self._robots:
            robot["x"] = robot.get("init_x", robot["x"])
            robot["y"] = robot.get("init_y", robot["y"])
            robot["theta"] = robot.get("init_theta", robot["theta"])
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
        if (self._anim_current is not None and
                self._anim_current.get("robot_idx") == robot_idx):
            return True
        return any(s.get("robot_idx") == robot_idx for s in self._anim_queue)

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

        if self._trails or self._active_trail:
            self._draw_trails(painter, scale, offset_x, offset_y)

        if self._robots:
            self._draw_robots(painter, scale, offset_x, offset_y)

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
                xx = float(command.split("#", 1)[1])
                ms = max(0.0, 100_000.0 - xx)  # match de 100s = 100 000 ms
                self._wait_until[robot_id] = time.monotonic() + ms / 1000.0
            except ValueError:
                pass

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


class SimulatorWindow(QMainWindow):
    """Fenêtre principale du simulateur."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulateur Robot 2D")

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

    def _on_reset_click(self):
        """Ferme les sous-fenêtres, efface les traces et remet les robots à l'origine."""
        if self._manual_window is not None:
            self._manual_window.close()
            self._manual_window = None
        if self._strategy_window is not None:
            self._strategy_window.close()
            self._strategy_window = None
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

