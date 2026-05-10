"""
Point d'entrée du RabbitControlCenter.

Lance les serveurs (logs + communication), le lecteur série des
12 interrupteurs, puis ouvre la fenêtre principale PySide6.
"""

import json
import logging
import os
import signal
import sys

# Permet `python rabbit_control_center/main.py` (sans PYTHONPATH=.) en ajoutant
# la racine du dépôt à sys.path avant les imports du package.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from rabbit_control_center.serial_reader import SerialSwitchReader
from rabbit_control_center.server import start_servers
from rabbit_control_center.state import ControlCenterState
from rabbit_control_center.ui import ControlCenterWindow


PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.join(PACKAGE_DIR, "config.json")
LOG_DIR = os.path.join(PACKAGE_DIR, "logs")


def load_config(path: str) -> dict:
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def setup_console_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def _install_signal_handlers(app: QApplication) -> QTimer:
    """
    `app.exec()` bloque dans du C++, donc Python ne traite jamais les signaux
    pendant ce temps : Ctrl+C et SIGTERM (`killall python`) sont ignorés. On
    installe deux handlers qui appellent `app.quit()`, et on déclenche un
    QTimer périodique no-op pour donner régulièrement la main à l'interpréteur
    Python afin qu'il livre les signaux.
    """
    def handler(signum, _frame):
        logging.getLogger(__name__).info("Signal %d reçu, arrêt en cours...", signum)
        app.quit()

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    wakeup = QTimer()
    wakeup.setInterval(500)
    wakeup.timeout.connect(lambda: None)
    wakeup.start()
    return wakeup


def main() -> int:
    setup_console_logging()
    config = load_config(DEFAULT_CONFIG_PATH)
    com_port = int(config.get("comPort", 4269))
    log_port = int(config.get("logPort", 9020))
    serial_cfg = config.get("serial", {}) or {}
    serial_port = serial_cfg.get("port")
    baud_rate = int(serial_cfg.get("baudRate", 115200))

    app = QApplication(sys.argv)
    # Quand la dernière fenêtre est fermée, on quitte l'event loop.
    app.setQuitOnLastWindowClosed(True)
    wakeup_timer = _install_signal_handlers(app)

    state = ControlCenterState()
    server_ctx = start_servers(state=state, log_dir=LOG_DIR,
                               com_port=com_port, log_port=log_port)

    serial_reader: SerialSwitchReader | None = None
    if serial_port:
        serial_reader = SerialSwitchReader(state=state, port=serial_port, baud_rate=baud_rate)
        serial_reader.start()
    else:
        logging.getLogger(__name__).warning(
            "Aucun port série configuré pour les interrupteurs (clé serial.port)."
        )

    window = ControlCenterWindow(state=state, config=config, server_ctx=server_ctx)
    window.showFullScreen()

    try:
        return app.exec()
    finally:
        wakeup_timer.stop()
        if serial_reader is not None:
            serial_reader.stop()


if __name__ == "__main__":
    sys.exit(main())
