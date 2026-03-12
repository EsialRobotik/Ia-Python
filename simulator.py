"""
Simulateur 2D pour robot - Affichage de la table de jeu.
Utilise PySide6 pour le rendu SVG natif.
"""

import sys
import os
import json
import math
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QComboBox, QLabel, QPushButton,
    QGridLayout, QDoubleSpinBox,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QRectF, QPointF, QTimer, QElapsedTimer, Qt, QLocale
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QPixmap

# Chemin du dossier simulation, relatif à ce fichier
SIMULATION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulation")

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
        self._table_size = None
        self._forbidden_zones: list = []
        self._dynamic_zones: list = []
        self._show_forbidden = False
        self._show_dynamic = False
        self._robots: list[dict] = []

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
        self._table_size = table_size
        self._zoom = 1.0
        self._pan = QPointF(0.0, 0.0)
        self._bg_cache = None
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

        if distance > 1:
            # Déplacement en ligne droite
            self._anim_queue.append({
                "type": "move",
                "robot_idx": robot_idx,
                "to_x": target_x,
                "to_y": target_y,
                "trail_color": QColor(trail_color),
            })

        # Rotation vers l'angle final
        self._anim_queue.append({
            "type": "rotate",
            "robot_idx": robot_idx,
            "to_theta": target_theta,
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
                "duration": max(dist / ANIM_MOVE_SPEED, 0.05),
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

        control_layout.addStretch()

        # --- Affichage de la table (SVG) ---
        self.table_widget = TableWidget()
        main_layout.addWidget(self.table_widget, stretch=1)

        self._manual_window: ManualControlWindow | None = None

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

    def _load_table(self, year: str):
        """Charge et affiche le SVG de la table pour l'année donnée."""
        # Fermer la fenêtre manuelle si ouverte
        if self._manual_window is not None:
            self._manual_window.close()
            self._manual_window = None
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

