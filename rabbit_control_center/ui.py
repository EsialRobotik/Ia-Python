"""
Interface graphique du RabbitControlCenter.

Deux vues empilées dans un QStackedWidget :
- Vue "idle" : tableau des robots (id, connecté, couleur), grille des
  12 interrupteurs (bp1..bp4 puis sw1..sw8).
- Vue "match" : table de jeu temps réel (réutilise le TableWidget du simulateur).
  Le passage en vue match est déclenché par le log "Match lancé".
"""

import ast
import os
import random
import re
from typing import Optional

from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QBrush, QPen, QPixmap, QImageReader

# Qt rejette par défaut les images dont la décompression dépasse 256 Mo, ce qui
# rend silencieusement nuls les PNG en haute résolution placés dans
# waiting-screens. On désactive la limite pour ce processus.
QImageReader.setAllocationLimit(0)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from rabbit_control_center.music_player import MusicPlayer
from rabbit_control_center.state import (
    ControlCenterState,
    SWITCH_COUNT,
    SWITCH_LABELS,
)
from simulator.simulator import (
    ROBOT_TRAIL_COLORS,
    TableWidget,
    get_available_years,
    get_table_size,
    get_table_svg_path,
    load_robots,
    load_table_zones,
)


# --- Mappage nom de couleur (FR) -> QColor d'affichage -----------------------

COLOR_NAME_MAP: dict[str, QColor] = {
    "jaune": QColor(255, 215, 0),
    "bleu": QColor(50, 110, 220),
    "rouge": QColor(220, 60, 60),
    "vert": QColor(50, 180, 80),
    "violet": QColor(160, 80, 200),
    "orange": QColor(255, 140, 0),
    "noir": QColor(40, 40, 40),
    "blanc": QColor(240, 240, 240),
    "rose": QColor(255, 110, 180),
    "cyan": QColor(0, 200, 220),
    "marron": QColor(120, 70, 30),
}


def color_for_name(name: Optional[str]) -> Optional[QColor]:
    if not name:
        return None
    return COLOR_NAME_MAP.get(name.strip().lower())


# --- Voyant lumineux pour interrupteur / connexion ---------------------------

class StateLight(QFrame):
    """Petit cercle coloré indiquant un état ON/OFF."""

    def __init__(self, on_color: QColor = QColor(80, 220, 100),
                 off_color: QColor = QColor(70, 70, 70),
                 size: int = 68, parent=None) -> None:
        super().__init__(parent)
        self._on = False
        self._on_color = on_color
        self._off_color = off_color
        self._diameter = size
        self.setFixedSize(QSize(size + 6, size + 6))

    def set_on(self, value: bool) -> None:
        if value == self._on:
            return
        self._on = value
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = self._on_color if self._on else self._off_color
        p.setBrush(QBrush(color))
        p.setPen(QPen(color.darker(140), 1))
        margin = 2
        p.drawEllipse(margin, margin,
                      self.width() - 2 * margin, self.height() - 2 * margin)


# --- Carré de couleur affiché dans le tableau --------------------------------

class ColorSwatch(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._color: Optional[QColor] = None
        self.setMinimumSize(121, 68)

    def set_color(self, color: Optional[QColor]) -> None:
        self._color = color
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(2, 2, -2, -2)
        if self._color is None:
            p.setBrush(QBrush(QColor(60, 60, 60)))
            p.setPen(QPen(QColor(110, 110, 110), 1))
            p.drawRoundedRect(rect, 4, 4)
            p.setPen(QColor(180, 180, 180))
            p.drawText(rect, Qt.AlignCenter, "—")
        else:
            p.setBrush(QBrush(self._color))
            p.setPen(QPen(self._color.darker(160), 1))
            p.drawRoundedRect(rect, 4, 4)


# --- Grille des 12 interrupteurs ---------------------------------------------

class SwitchPanel(QWidget):
    """
    Grille 4×3 (12 interrupteurs) où chaque case occupe 2 colonnes du
    QGridLayout : pastille puis label. Les pastilles sont donc alignées
    verticalement entre les rangées (col 0, 2, 4) et les labels également
    (col 1, 3, 5).
    """

    COLS = 3
    ROWS = SWITCH_COUNT // 3  # 4

    def __init__(self, labels: Optional[list[str]] = None, parent=None) -> None:
        super().__init__(parent)
        if labels is None or len(labels) != SWITCH_COUNT:
            labels = list(SWITCH_LABELS)
        self._labels = labels

        # Le panel doit pouvoir se rétrécir librement pour respecter le
        # facteur de stretch 60/40 du parent même sur petit écran.
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Interrupteurs")
        title.setStyleSheet("font-size: 21pt; font-weight: bold;")
        layout.addWidget(title)
        layout.addStretch()

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        self._lights: list[StateLight] = []
        for idx in range(SWITCH_COUNT):
            row = idx // self.COLS
            col = idx % self.COLS

            light = StateLight(size=52)
            self._lights.append(light)
            grid.addWidget(light, row, col * 2,
                           alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            lbl = QLabel(labels[idx])
            lbl.setStyleSheet("font-family: monospace; font-size: 15pt;")
            grid.addWidget(lbl, row, col * 2 + 1,
                           alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Centre la grille horizontalement (stretches de chaque côté)
        grid_row = QHBoxLayout()
        grid_row.addStretch()
        grid_row.addLayout(grid)
        grid_row.addStretch()
        layout.addLayout(grid_row)
        layout.addStretch()

    def update_states(self, values: list[bool]) -> None:
        for light, on in zip(self._lights, values):
            light.set_on(on)


# --- Tableau des robots ------------------------------------------------------

class RobotsTable(QTableWidget):
    """Tableau : Robot | Connecté | Couleur."""

    def __init__(self, parent=None) -> None:
        super().__init__(0, 3, parent)
        self.setHorizontalHeaderLabels(["Robot", "Connecté", "Couleur"])
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(91)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        header = self.horizontalHeader()
        # Colonnes de largeur égale (toutes en Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("QHeaderView::section { font-size: 18pt; padding: 8px; }")
        self._row_index: dict[str, int] = {}
        self._lights: dict[str, StateLight] = {}
        self._swatches: dict[str, ColorSwatch] = {}

    @staticmethod
    def _centered(widget: QWidget) -> QWidget:
        """Enveloppe un widget dans un QWidget centré horizontalement et verticalement."""
        holder = QWidget()
        layout = QHBoxLayout(holder)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch()
        return holder

    def populate(self, robot_ids: list[str]) -> None:
        self.clearContents()
        self.setRowCount(len(robot_ids))
        self._row_index.clear()
        self._lights.clear()
        self._swatches.clear()

        for row, robot_id in enumerate(robot_ids):
            self._row_index[robot_id] = row

            id_item = QTableWidgetItem(robot_id)
            id_item.setFont(QFont("Sans", 26, QFont.Weight.Bold))
            color_idx = row % len(ROBOT_TRAIL_COLORS)
            id_item.setForeground(ROBOT_TRAIL_COLORS[color_idx])
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row, 0, id_item)

            # Voyant connecté centré (StateLight réduit de 10% par rapport à la grille des switches)
            light = StateLight(on_color=QColor(80, 220, 100), off_color=QColor(180, 60, 60), size=61)
            self._lights[robot_id] = light
            self.setCellWidget(row, 1, self._centered(light))

            # Carré de couleur centré
            swatch = ColorSwatch()
            self._swatches[robot_id] = swatch
            self.setCellWidget(row, 2, self._centered(swatch))

    def update_robot(self, robot_id: str, connected: bool, color_name: Optional[str]) -> None:
        light = self._lights.get(robot_id)
        if light is not None:
            light.set_on(connected)
        swatch = self._swatches.get(robot_id)
        if swatch is not None:
            swatch.set_color(color_for_name(color_name))


# --- Vue idle (avant match) --------------------------------------------------

class IdleView(QWidget):
    def __init__(self, switch_labels: Optional[list[str]] = None, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Barre du haut : titre + année + boutons Ready / Quitter sur une ligne
        top_row = QHBoxLayout()

        title = QLabel("Rabbit Control Center")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        top_row.addWidget(title)
        top_row.addSpacing(24)

        top_row.addWidget(QLabel("Année :"))
        self.year_combo = QComboBox()
        for year in get_available_years():
            self.year_combo.addItem(year)
        if self.year_combo.count() > 0:
            self.year_combo.setCurrentIndex(self.year_combo.count() - 1)
        top_row.addWidget(self.year_combo)
        top_row.addStretch()

        button_style = "QPushButton { font-size: 14pt; padding: 8px 18px; }"

        bp1_label = (switch_labels or SWITCH_LABELS)[0]
        self.btn_bp1 = QPushButton(bp1_label)
        self.btn_bp1.setStyleSheet(button_style)
        top_row.addWidget(self.btn_bp1)

        self.btn_quit = QPushButton("Quitter")
        self.btn_quit.setStyleSheet(button_style)
        top_row.addWidget(self.btn_quit)

        layout.addLayout(top_row)

        # Bandeau : tableau robots à gauche, interrupteurs à droite
        body = QHBoxLayout()
        layout.addLayout(body, stretch=1)

        robots_panel = QVBoxLayout()
        robots_title = QLabel("Robots")
        robots_title.setStyleSheet("font-size: 19pt; font-weight: bold;")
        robots_panel.addWidget(robots_title)
        self.robots_table = RobotsTable()
        robots_panel.addWidget(self.robots_table, stretch=1)
        body.addLayout(robots_panel, stretch=60)

        self.switch_panel = SwitchPanel(labels=switch_labels)
        body.addWidget(self.switch_panel, stretch=40)

    def current_year(self) -> Optional[str]:
        return self.year_combo.currentText() or None


# --- Vue d'attente (slideshow PNG) -------------------------------------------

class WaitingScreenView(QWidget):
    """
    Affiche un slideshow d'images PNG sur fond rose `#FA3296`.
    Les images sont tirées au sort dans `images_dir` et changent toutes les
    `interval_seconds` secondes. Le widget capte les clics pour permettre à
    l'utilisateur de revenir à la vue précédente (géré par la fenêtre parent).
    """

    def __init__(self, images_dir: str, interval_seconds: float = 20.0,
                 background: str = "#FA3296", parent=None) -> None:
        super().__init__(parent)
        self._images_dir = images_dir
        self._interval_ms = max(1000, int(interval_seconds * 1000))
        self._files: list[str] = []
        self._last_path: Optional[str] = None
        # Cache des QPixmap déjà décodés et scalés. Les PNG très haute résolution
        # peuvent prendre plusieurs secondes à décompresser sur Raspberry Pi ;
        # sans ce cache, chaque tick du timer redéclenche un décodage complet
        # et l'intervalle effectif dérive bien au-delà de `interval_seconds`.
        self._pixmap_cache: dict[str, QPixmap] = {}

        self.setAutoFillBackground(True)
        self.setStyleSheet(f"background-color: {background};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setStyleSheet(f"background-color: {background}; color: white; font-size: 18pt;")
        layout.addWidget(self._image_label)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._show_random_image)

    # --- API publique --------------------------------------------------------

    def start(self) -> None:
        self._refresh_file_list()
        self._show_random_image()
        self._timer.start(self._interval_ms)
        # Précharge les autres images en tâche de fond — chaque image est
        # décodée dans un tick séparé du loop pour ne pas bloquer l'UI.
        QTimer.singleShot(0, self._prefetch_next)

    def stop(self) -> None:
        self._timer.stop()

    # --- Internes ------------------------------------------------------------

    def _refresh_file_list(self) -> None:
        try:
            entries = os.listdir(self._images_dir)
        except OSError:
            self._files = []
            return
        self._files = sorted(
            os.path.join(self._images_dir, name)
            for name in entries
            if name.lower().endswith(".png")
        )
        # Nettoie les entrées de cache pour des fichiers disparus
        self._pixmap_cache = {
            p: pm for p, pm in self._pixmap_cache.items() if p in self._files
        }

    def _prefetch_next(self) -> None:
        """Charge en cache la prochaine image non encore décodée."""
        if not self._timer.isActive():
            return
        missing = [p for p in self._files if p not in self._pixmap_cache]
        if not missing:
            return
        self._load_scaled(missing[0])
        QTimer.singleShot(50, self._prefetch_next)

    def _show_random_image(self) -> None:
        self._refresh_file_list()
        if not self._files:
            self._image_label.setPixmap(QPixmap())
            self._image_label.setText(
                f"Aucune image PNG dans\n{self._images_dir}"
            )
            return

        # Boucle de sélection : si une image est illisible (Qt rejette ou fichier
        # corrompu), on l'écarte et on tire à nouveau, jusqu'à trouver une
        # image valide ou épuiser les candidats.
        candidates = [p for p in self._files if p != self._last_path] or list(self._files)
        random.shuffle(candidates)
        for path in candidates:
            pixmap = self._load_scaled(path)
            if pixmap is None:
                continue
            self._last_path = path
            self._display_pixmap(pixmap)
            return

        self._image_label.setPixmap(QPixmap())
        self._image_label.setText(
            "Aucune image PNG lisible dans\n" + self._images_dir
        )

    def _target_size(self) -> QSize:
        size = self._image_label.size()
        if size.width() <= 1 or size.height() <= 1:
            size = self.size()
        if size.width() <= 1 or size.height() <= 1:
            size = QSize(1280, 720)
        return size

    def _load_scaled(self, path: str) -> Optional[QPixmap]:
        """
        Décode un PNG via `QImageReader.setScaledSize` (pré-scalage pendant
        la décompression : évite ~1 Go de RAM pour un 14584×16667). Le résultat
        est mis en cache : un même fichier n'est jamais décodé deux fois.
        """
        cached = self._pixmap_cache.get(path)
        if cached is not None:
            return cached

        target = self._target_size()
        reader = QImageReader(path)
        reader.setAutoTransform(True)
        src = reader.size()
        if src.isValid() and src.width() > 0 and src.height() > 0:
            ratio = min(target.width() / src.width(), target.height() / src.height())
            if 0 < ratio < 1:
                scaled_w = max(1, int(src.width() * ratio))
                scaled_h = max(1, int(src.height() * ratio))
                reader.setScaledSize(QSize(scaled_w, scaled_h))
        image = reader.read()
        if image.isNull():
            return None
        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            return None
        self._pixmap_cache[path] = pixmap
        return pixmap

    def _display_pixmap(self, pixmap: QPixmap) -> None:
        """Affiche un QPixmap déjà chargé en l'ajustant à la taille du widget."""
        target = self._target_size()
        if pixmap.size() != target:
            pixmap = pixmap.scaled(
                target,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        self._image_label.setPixmap(pixmap)

    def resizeEvent(self, event):
        # Re-scale la dernière image depuis le cache (pas de relecture disque).
        super().resizeEvent(event)
        if self._last_path:
            cached = self._pixmap_cache.get(self._last_path)
            if cached is not None:
                self._display_pixmap(cached)


# --- Vue match (table temps réel) --------------------------------------------

class MatchView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Bandeau : titre + bouton retour
        bar = QHBoxLayout()
        title = QLabel("Match en cours")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        bar.addWidget(title)
        bar.addStretch()
        self.btn_back = QPushButton("← Retour")
        bar.addWidget(self.btn_back)
        layout.addLayout(bar)

        # En-têtes robots colorés
        self._headers_row = QHBoxLayout()
        layout.addLayout(self._headers_row)

        self.table_widget = TableWidget()
        layout.addWidget(self.table_widget, stretch=1)

    def load_year(self, year: str) -> None:
        svg_path = get_table_svg_path(year)
        if not os.path.isfile(svg_path):
            return
        table_size = get_table_size(year)
        self.table_widget.load(svg_path, table_size)
        forbidden, dynamic = load_table_zones(year)
        self.table_widget.set_zones(forbidden, dynamic)
        robots = load_robots(year)
        self.table_widget.set_robots(robots)
        self._rebuild_headers(robots)

    def _rebuild_headers(self, robots: list[dict]) -> None:
        # Vide la rangée
        while self._headers_row.count():
            item = self._headers_row.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        for robot in robots:
            color = robot.get("trail_color", ROBOT_TRAIL_COLORS[0])
            lbl = QLabel(f"● {robot['id']}")
            lbl.setStyleSheet(f"color: {color.name()}; font-weight: bold;")
            self._headers_row.addWidget(lbl)
        self._headers_row.addStretch()

    # --- Réception d'évènements logs --------------------------------------

    def handle_position(self, robot_id: str, message: str) -> None:
        try:
            dict_str = message[len("Position :"):].strip()
            pos = ast.literal_eval(dict_str)
            x = float(pos["x"])
            y = float(pos["y"])
            theta = float(pos["theta"])
        except (ValueError, KeyError, SyntaxError):
            return
        color = self._color_for_robot(robot_id)
        self.table_widget.animate_robot_move(robot_id, x, y, theta, color)

    def handle_detection(self, robot_id: str, message: str) -> None:
        color = self._color_for_robot(robot_id)
        m = re.search(r'at position \((-?\d+),(-?\d+)\)', message)
        if m:
            sx, sy = self._robot_position(robot_id)
            self.table_widget.add_detection(
                float(m.group(1)), float(m.group(2)), color,
                source_x=sx, source_y=sy,
            )
            return
        m = re.search(r'Lidar detection: Position\(x=(-?\d+), y=(-?\d+)', message)
        if m:
            self.table_widget.add_detection(float(m.group(1)), float(m.group(2)), color)

    def _color_for_robot(self, robot_id: str) -> QColor:
        for r in self.table_widget._robots:
            if r["id"] == robot_id:
                return r.get("trail_color", QColor(200, 200, 200))
        for r in self.table_widget._robots:
            if r["id"] in robot_id:
                return r.get("trail_color", QColor(200, 200, 200))
        return QColor(200, 200, 200)

    def _robot_position(self, robot_id: str) -> tuple[Optional[float], Optional[float]]:
        for r in self.table_widget._robots:
            if r["id"] == robot_id:
                return r["x"], r["y"]
        return None, None


# --- Fenêtre principale ------------------------------------------------------

class ControlCenterWindow(QMainWindow):
    def __init__(self, state: ControlCenterState, config: Optional[dict] = None,
                 server_ctx=None) -> None:
        super().__init__()
        self.setWindowTitle("Rabbit Control Center")
        self.state = state
        self._config = config or {}
        self._server_ctx = server_ctx

        switch_labels = self._config.get("switchLabels")
        if not isinstance(switch_labels, list) or len(switch_labels) != SWITCH_COUNT:
            switch_labels = list(SWITCH_LABELS)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.idle_view = IdleView(switch_labels=switch_labels)
        self.match_view = MatchView()

        # Vue d'attente : dossier d'images relatif au package par défaut
        images_dir = self._config.get("waitingScreensDir") or "waiting-screens"
        if not os.path.isabs(images_dir):
            images_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), images_dir
            )
        self.waiting_view = WaitingScreenView(
            images_dir=images_dir,
            interval_seconds=float(self._config.get("waitingScreenIntervalSeconds", 20)),
            background=str(self._config.get("waitingScreenBackground", "#FA3296")),
        )

        self.stack.addWidget(self.idle_view)
        self.stack.addWidget(self.waiting_view)
        self.stack.addWidget(self.match_view)

        # Lecteur audio : bp3 = piste précédente, bp4 = suivante,
        # sw2 toggle on/off ; le passage en match force un démarrage aléatoire.
        music_dir = self._config.get("musicDir") or "music"
        if not os.path.isabs(music_dir):
            music_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), music_dir
            )
        self.music_player = MusicPlayer(music_dir=music_dir, parent=self)

        self.idle_view.year_combo.currentTextChanged.connect(self._on_year_changed)
        self.idle_view.btn_bp1.clicked.connect(self._cycle_mode)
        self.idle_view.btn_quit.clicked.connect(self.close)
        self.match_view.btn_back.clicked.connect(self._show_idle)

        # État local pour suivre les transitions des boutons / switches
        self._last_bp1: bool = False
        self._last_bp3: bool = False
        self._last_bp4: bool = False
        self._last_sw_music: bool = False
        self._waiting_active: bool = False
        self._switches_initialized: bool = False

        # Connecter les signaux d'état
        self.state.robot_state_changed.connect(self._on_robot_state_changed)
        self.state.switches_changed.connect(self._on_switches_changed)
        self.state.match_started.connect(self._show_match)
        self.state.log_record_parsed.connect(self._on_log_record)

        # Initialiser sur l'année courante
        year = self.idle_view.current_year()
        if year:
            self._load_year(year)

    # --- Année ---------------------------------------------------------------

    def _on_year_changed(self, year: str) -> None:
        if year:
            self._load_year(year)

    def _load_year(self, year: str) -> None:
        # Récupérer la liste des robots depuis simulator/<year>/init.json
        robots = load_robots(year)
        robot_ids = [r["id"] for r in robots]
        self.idle_view.robots_table.populate(robot_ids)
        # Pré-affecter les états déjà connus
        for rid in robot_ids:
            rstate = self.state.model.robots.get(rid)
            connected = rstate.connected if rstate else False
            color = rstate.color if rstate else None
            self.idle_view.robots_table.update_robot(rid, connected, color)
        # Charger la table dans la vue match
        self.match_view.load_year(year)

    # --- Bascules de vues ----------------------------------------------------

    def _show_match(self) -> None:
        if self._waiting_active:
            self._stop_waiting_screen()
        self.stack.setCurrentWidget(self.match_view)
        # En mode match, musique démarrée automatiquement quoi qu'il arrive.
        # Un flip ON→OFF du switch musique coupera ensuite normalement.
        if not self.music_player.is_playing():
            self.music_player.play(random_start=True)
        # sw8 (SoloPami, index 11) : si activé au lancement du match, on
        # diffuse `add-flag#solo-pami` à tous les robots connectés.
        switches = self.state.model.switches
        sw_solo_pami = bool(switches[11]) if len(switches) > 11 else False
        if sw_solo_pami and self._server_ctx is not None:
            self._server_ctx.broadcast_to_robots("add-flag#solo-pami")

    def _show_idle(self) -> None:
        self.state.reset_match()
        if self._waiting_active:
            self._stop_waiting_screen()
        self.stack.setCurrentWidget(self.idle_view)
        # En tableau de bord, musique uniquement si le switch est ON.
        self._sync_music_to_switch()

    def _start_waiting_screen(self) -> None:
        if self._waiting_active:
            return
        self._waiting_active = True
        self.waiting_view.start()
        self.stack.setCurrentWidget(self.waiting_view)
        # En écran d'attente, même règle qu'idle : musique = état du switch.
        self._sync_music_to_switch()

    def _sync_music_to_switch(self) -> None:
        """Aligne la musique sur l'état actuel du switch musique (index 5)."""
        switches = self.state.model.switches
        sw_music = bool(switches[5]) if len(switches) > 5 else False
        if sw_music and not self.music_player.is_playing():
            self.music_player.play(random_start=True)
        elif not sw_music and self.music_player.is_playing():
            self.music_player.stop()

    def _stop_waiting_screen(self) -> None:
        if not self._waiting_active:
            return
        self._waiting_active = False
        self.waiting_view.stop()
        # Retour à idle si on n'est pas passé en match entre temps
        if self.stack.currentWidget() is self.waiting_view:
            self.stack.setCurrentWidget(self.idle_view)

    def _toggle_waiting_screen(self) -> None:
        if self._waiting_active:
            self._stop_waiting_screen()
        else:
            self._start_waiting_screen()

    def _cycle_mode(self) -> None:
        """
        Bouton bp1 / bouton "Ready" : avance dans le cycle de vues
        idle → waiting → match → idle → … à chaque pression (front montant).
        """
        current = self.stack.currentWidget()
        if current is self.match_view:
            self._show_idle()
        elif current is self.waiting_view:
            # Passe en mode match (déclenche aussi le démarrage musique)
            self.state.declare_match_started()
        else:
            self._start_waiting_screen()

    # --- Évènements d'état ---------------------------------------------------

    def _on_robot_state_changed(self, robot_id: str) -> None:
        rstate = self.state.model.robots.get(robot_id)
        if rstate is None:
            return
        # Si le robot n'est pas dans la liste actuelle (année différente), on ignore.
        self.idle_view.robots_table.update_robot(robot_id, rstate.connected, rstate.color)

    def _on_switches_changed(self, values: list) -> None:
        # Mise à jour visuelle des voyants
        self.idle_view.switch_panel.update_states(values)
        if not values:
            return

        # Indices : bp1=0, bp2=1, bp3=2, bp4=3, sw1=4, sw_music=5, ..., sw8=11
        bp1 = bool(values[0])
        bp3 = bool(values[2])
        bp4 = bool(values[3])
        sw_music = bool(values[5])

        # On ignore les transitions au tout premier appel pour ne pas
        # déclencher d'actions sur l'état initial des switches.
        if not self._switches_initialized:
            self._last_bp1 = bp1
            self._last_bp3 = bp3
            self._last_bp4 = bp4
            self._last_sw_music = sw_music
            self._switches_initialized = True
            return

        # bp1 (bouton poussoir) : impulsion sur front montant.
        # Chaque pression cycle dans les vues : idle → waiting → match → idle.
        if bp1 and not self._last_bp1:
            self._cycle_mode()

        # bp3 / bp4 : impulsions sur front montant pour piste précédente / suivante
        if bp3 and not self._last_bp3:
            self.music_player.prev()
        if bp4 and not self._last_bp4:
            self.music_player.next()

        # Switch musique : synchronisation directe.
        # ON → s'assurer que la musique joue ; OFF → couper.
        # Cette règle s'applique aussi en mode match (où la musique a été
        # auto-démarrée à l'entrée) : un flip ON→OFF coupe, OFF→ON→OFF coupe,
        # OFF→ON ne fait rien si la musique tourne déjà.
        if sw_music != self._last_sw_music:
            if sw_music:
                if not self.music_player.is_playing():
                    self.music_player.play(random_start=True)
            else:
                self.music_player.stop()

        self._last_bp1 = bp1
        self._last_bp3 = bp3
        self._last_bp4 = bp4
        self._last_sw_music = sw_music

    def _on_log_record(self, _ts: str, who: str, _level: str, message: str) -> None:
        if self.stack.currentWidget() is not self.match_view:
            return
        if message.startswith("Position :"):
            self.match_view.handle_position(who, message)
        elif "detected an obstacle at position" in message or message.startswith("Lidar detection:"):
            self.match_view.handle_detection(who, message)

    def closeEvent(self, event):
        """Coupe la musique avant de laisser la fenêtre se fermer."""
        try:
            self.music_player.stop()
        except Exception:
            pass
        super().closeEvent(event)
