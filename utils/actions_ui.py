import argparse
import logging.handlers
import time

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Label, Log, Placeholder

from ia.actions.action_repository_factory import ActionRepositoryFactory
from ia.actions.serial_port import SerialPort
from ia.api.ax12.ax12_link_serial import AX12LinkSerial
from ia.api.camera import Camera
from ia.utils.config_loader import load_config
from ia.utils.robot import Robot


class Header(Placeholder):
    def set_text(self, text: str) -> None:
        self._renderables["default"] = text
        self.refresh()


class ActionsUi(App):
    CSS = """
    Screen { align: center middle; }
    Header { height: 3; dock: top; }
    Footer { height: 3; dock: bottom; }
    Horizontal { height: auto; align: left top; }
    .columns-container {
        width: 1fr;
        height: 1fr;
        border: solid white;
    }
    .column1 {
        width: 40%;
        height: 100%;
    }
    .column2 {
        width: 60%;
        height: 100%;
    }
    .button {
        margin: 0 1;
        height: 3;
        width: 1fr;
    }
    .footer-button {
        margin: 0 2;
        height: 3;
    }
    .logs {
        padding: 1;
        border: solid white;
    }
    """

    def __init__(self, config_data: dict) -> None:
        super().__init__()
        self.config_data = config_data
        self.ax12_link_serial = None
        self.serial_ports: dict[str, SerialPort] = {}
        self.camera = None
        self._action_repo = None
        self._busy = False

    def _build_repository(self) -> None:
        actions_config = self.config_data.get("actions", {})
        if actions_config.get("ax12") is not None:
            self.ax12_link_serial = AX12LinkSerial(
                serial_port=actions_config["ax12"]["serialPort"],
                baud_rate=actions_config["ax12"]["baudRate"],
            )
        if actions_config.get("actuators") is not None:
            for actuator_config in actions_config["actuators"]:
                if actuator_config["type"] == "serial":
                    port_id = actuator_config.get("id", str(len(self.serial_ports)))
                    self.serial_ports[port_id] = SerialPort(
                        actuator_config["serialPort"], actuator_config["baudRate"]
                    )
        if actions_config.get("camera") is not None:
            self.camera = Camera()
        self._action_repo = ActionRepositoryFactory.from_json_files(
            actions_config["dataDir"],
            self.ax12_link_serial,
            self.serial_ports,
            camera=self.camera,
        )

    def compose(self) -> ComposeResult:
        self._build_repository()
        # Le repo stocke à la fois l'id de l'action et ses alias, pointant vers
        # le même objet. On garde uniquement la première clé rencontrée par
        # objet (ordre d'insertion = id avant alias dans la fabrique).
        seen: dict[int, str] = {}
        for key, action in self._action_repo._actions.items():
            seen.setdefault(id(action), key)
        self._action_names = sorted(seen.values())

        yield Horizontal(
            Button("Quitter", id="quit", variant="error", classes="footer-button"),
            Label(
                f"{len(self._action_names)} actions chargées",
                id="status",
                expand=True,
            ),
            id="footer",
        )
        yield Horizontal(
            Vertical(
                Header("Actions disponibles"),
                VerticalScroll(
                    *[
                        Button(name, id=f"action_{i}", classes="button")
                        for i, name in enumerate(self._action_names)
                    ],
                ),
                classes="column1",
            ),
            Vertical(
                Header("Logs"),
                Log(classes="logs", id="logs"),
                classes="column2",
            ),
            classes="columns-container",
        )

    def _log_line(self, message: str) -> None:
        self.query_one("#logs", Log).write_line(message)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.exit()
            return
        if event.button.id is None or not event.button.id.startswith("action_"):
            return
        if self._busy:
            self.notify("Une action est déjà en cours…", severity="warning", timeout=3)
            return

        idx = int(event.button.id.split("_", 1)[1])
        name = self._action_names[idx]
        self._busy = True
        self.query_one("#status", Label).update(f"Exécution : {name}…")
        self._log_line(f"▶ {name}")
        self.run_worker(
            self._run_action(name),
            exclusive=True,
            thread=True,
            name=f"action_{name}",
        )

    def _run_action(self, name: str):
        def task():
            try:
                action = self._action_repo.get_action(name)
                action.reset()
                action.execute()
                start = time.monotonic()
                while not action.finished():
                    time.sleep(0.01)
                elapsed_ms = int((time.monotonic() - start) * 1000)
                self.call_from_thread(self._log_line, f"✔ {name} : {elapsed_ms} ms")
                self.call_from_thread(
                    self.query_one("#status", Label).update,
                    f"{name} terminée en {elapsed_ms} ms",
                )
            except Exception as e:
                self.call_from_thread(self._log_line, f"✖ {name} : {e}")
                self.call_from_thread(
                    self.query_one("#status", Label).update,
                    f"Erreur sur {name} : {e}",
                )
            finally:
                self._busy = False

        return task


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interface de test des actions.")
    parser.add_argument("year", type=int, help="Année de la config")
    parser.add_argument("robot", type=str, help="Robot (cf. enum Robot)")
    args = parser.parse_args()

    logging.getLogger("").setLevel(logging.DEBUG)
    file_handler = logging.handlers.RotatingFileHandler(
        filename="logs/log.log", backupCount=50
    )
    file_handler.doRollover()
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logging.getLogger().addHandler(file_handler)

    robot = Robot(args.robot)
    config_data = load_config(args.year, robot.value)

    ActionsUi(config_data=config_data).run()