import argparse
import json

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Placeholder, Button, Log, Input

from ia.asservissement.asserv import Asserv
from ia.utils.position import Position
from ia.utils.robot import Robot


class Header(Placeholder):
    def set_text(self, text: str) -> None:
        """Met à jour le texte affiché dans le Header."""
        self._renderables["default"] = text
        self.refresh()

class Footer(Horizontal):
    pass

class ColumnsContainer(Horizontal):
    pass

class AsservUi(App):
    CSS = """
    Screen { align: center middle; }
    Header {
        height: 3;
        dock: top;
    }
    Footer {
        height: 3;
        dock: bottom;
    }
    Horizontal {
        height: auto;
        align: left top;
    }
    .columns-container {
        width: 1fr;
        height: 1fr;
        border: solid white;
    }
    .column1 {
        width: 75%;
        height: 100%;
    }
    .column2 {
        width: 25%;
        height: 100%;
    }
    .button {
        margin: 0 2;
        height: 3;
    }
    .logs {
        padding: 2;
        border: solid white;
    }
    .margin-top {
        margin-top: 1;
    }
    Static {
        width: 10;
        height: 3;
        content-align: center middle;
    }
    Input {
        width: 10;
        height: 3;
        text-align: center;
    }
    """

    def __init__(self, config_data: dict) -> None:
        super().__init__()
        self.asserv = Asserv(
            serial_port=config_data['asserv']['serialPort'],
            baud_rate=config_data['asserv']['baudRate'],
            gostart_config=config_data['asserv']['goStart'],
        )
        self.color0 = config_data['table']['color0']
        self.color3000 = config_data['table']['color3000']

    def compose(self) -> ComposeResult:
        yield Header(id="header")
        yield Footer(
            Button("Quitter", id="quit", variant="error", classes="button"),
            id="footer"
        )
        yield Horizontal(
            Vertical(
                Header("Contrôle du robot"),
                Horizontal(
                    Button(f"Callage {self.color0}", id="gostart0", variant="primary", classes="button"),
                    Button(f"Callage {self.color3000}", id="gostart3000", variant="primary", classes="button"),
                    Button("Arrêt d'urgence", id="emergency_stop", variant="error", classes="button"),
                    Button("Reset arrêt d'urgence", id="reset_stop", variant="success", classes="button"),
                    classes="margin-top",
                ),
                Horizontal(
                    Button("Low speed", id="low_speed", variant="warning", classes="button"),
                    Button("Normal speed", id="normal_speed", variant="success", classes="button"),
                    classes="margin-top",
                ),
                Horizontal(
                    Horizontal(
                        Static("GoTo"),
                        Input(placeholder="X", id="goto_x"),
                        Input(placeholder="Y", id="goto_y"),
                        Button("GoTo", id="goto", variant="primary", classes="button"),
                    ),
                    Horizontal(
                        Static("Face"),
                        Input(placeholder="X", id="face_x"),
                        Input(placeholder="Y", id="face_y"),
                        Button("Face", id="face", variant="primary", classes="button"),
                    ),
                    classes="margin-top",
                ),
                Horizontal(
                    Horizontal(
                        Static("Go"),
                        Input(placeholder="Distance", id="go_dist"),
                        Button("Go", id="go", variant="primary", classes="button"),
                    ),
                    Horizontal(
                        Static("Turn"),
                        Input(placeholder="Degree", id="turn_degree"),
                        Button("Turn", id="turn", variant="primary", classes="button"),
                    ),
                    classes="margin-top",
                ),
                classes="column1",
            ),
            Vertical(
                Header("Logs"),
                Log(classes="logs"),
                classes="column2",
            ),
            classes="columns-container",
        )

    def on_ready(self) -> None:
        self.update_position()
        self.set_interval(0.1, self.update_position())

    def update_position(self) -> None:
        self.query_one(Header).set_text(f"Position du robot : {self.asserv.position}")
        log = self.query_one(Log)
        log.write_line(self.asserv.last_log)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'quit':
            self.exit()
        elif event.button.id == 'goto':
            x = self.query_one("#goto_x").value
            y = self.query_one("#goto_y").value
            self.asserv.go_to(Position(x, y))
        elif event.button.id == 'face':
            x = self.query_one("#face_x").value
            y = self.query_one("#face_y").value
            self.asserv.face(Position(x, y))
        elif event.button.id == 'go':
            dist = self.query_one("#go_dist").value
            self.asserv.go(dist)
        elif event.button.id == 'turn':
            degree = self.query_one("#turn_degree").value
            self.asserv.turn(degree)
        elif event.button.id == 'gostart0':
            self.asserv.go_start(self.color0)
        elif event.button.id == 'gostart3000':
            self.asserv.go_start(self.color3000)
        elif event.button.id == 'emergency_stop':
            self.asserv.emergency_stop()
        elif event.button.id == 'reset_stop':
            self.asserv.emergency_reset()
        elif event.button.id == 'low_speed':
            self.asserv.enable_low_speed(True)
        elif event.button.id == 'normal_speed':
            self.asserv.enable_low_speed(False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a year.")
    parser.add_argument("year", type=int, help="Year in integer format")
    parser.add_argument("robot", type=str, help="Robot type from Robot enum")
    args = parser.parse_args()
    robot = Robot(args.robot)

    with open(f'config/{args.year}/{robot.value}/config.json') as config_file:
        config_data = json.load(config_file)
        config_file.close()
        app = AsservUi(
            config_data=config_data,
        )
        app.run()