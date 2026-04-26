import argparse
import json
import logging.handlers

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Placeholder, Button, Log, Input, Label, RadioButton, Rule

from ia.asservissement.asserv import Asserv
from ia.utils.position import Position
from ia.utils.robot import Robot


def is_float(element: any) -> bool:
    # If you expect None to be passed:
    if element is None:
        return False
    try:
        float(element)
        return True
    except ValueError:
        return False


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
        width: 55%;
        height: 100%;
    }
    .column2 {
        width: 45%;
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
    .currentId{
        width: 55%;
    }

    .orbitalStyle{
        width: 20%;
    }
    """

    def __init__(self, config_data: dict) -> None:
        super().__init__()
        self.asserv = Asserv(
            serial_port=config_data['asserv']['serialPort'],
            baud_rate=config_data['asserv']['baudRate'],
            gostart_config=config_data['asserv']['goStart'],
        )
        self.queueNoStopMsg = []
        self.current_msg_id = 0

    def compose(self) -> ComposeResult:
        yield Footer(
            Horizontal(
                Button("Quitter", id="quit", variant="error", classes="button"),
                Label("Cmd ID courante : 0", expand=True, classes="currentId", id="current_id"),
            ),
            id="footer"
        )
        yield Horizontal(
            Vertical(
                Header("Contrôle du robot"),
                Horizontal(
                    Button("Arrêt d'urgence", id="emergency_stop", variant="error", classes="button"),
                    Button("Reset arrêt d'urgence", id="reset_stop", variant="success", classes="button"),
                    Button("Low speed", id="low_speed", variant="warning", classes="button"),
                    Button("Normal speed", id="normal_speed", variant="success", classes="button"),
                    classes="margin-top",
                ),
                Rule(),
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
                Horizontal(
                    Horizontal(
                        Static("GoTo"),
                        Input(placeholder="X", id="goto_x"),
                        Input(placeholder="Y", id="goto_y"),
                        Button("GoTo", id="goto", variant="primary", classes="button"),
                    ),
                    Horizontal(
                        Static("GoToBack"),
                        Input(placeholder="X", id="gotoback_x"),
                        Input(placeholder="Y", id="gotoback_y"),
                        Button("GoToBack", id="gotoback", variant="primary", classes="button"),
                    ),
                    classes="margin-top",
                ),
                Horizontal(
                    Horizontal(
                        Static("Face"),
                        Input(placeholder="X", id="face_x"),
                        Input(placeholder="Y", id="face_y"),
                        Button("Face", id="face", variant="primary", classes="button"),
                    ),
                    classes="margin-top",
                ),
                Rule(),
                Horizontal(
                    Static("Orbital Turn"),
                    Input(placeholder="Degree", id="orbital_angle", classes="orbitalStyle"),
                    RadioButton("Forward ?", value=True, classes="orbitalStyle", id="orbital_fw"),
                    RadioButton("To the right ?", value=True, classes="orbitalStyle", id="orbital_right"),
                    Button("Orbital turn", id="orbital", variant="primary", classes="button"),
                ),
                Rule(),
                Horizontal(
                    Static("GoToNoStop"),
                    Input(placeholder="X", id="gotonostop_x"),
                    Input(placeholder="Y", id="gotonostop_y"),
                    Button("Queue GoTo NoStop", id="gotonostop", variant="primary", classes="button"),
                ),
                Horizontal(
                    Label(f"Nombre de commande NoStop en file: {len(self.queueNoStopMsg)}", expand=True,
                          classes="currentId", id="nb_nostop_queued"),
                    Button("Send queued NoStop", id="nostopsend", variant="primary", classes="button"),
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

    def on_ready(self) -> None:
        self.update_position()
        self.set_interval(1 / 8, self.update_position)

    def update_position(self) -> None:
        log = self.query_one("#logs")
        log.write_line(
            f"X:{self.asserv.position.x} Y:{self.asserv.position.y} \u03B8:{self.asserv.position.theta:.3f} / cmd Id:{self.asserv.last_received_command_id} status:{self.asserv.asserv_status} nb pending:{self.asserv.queue_size} / Motor left:{self.asserv.motor_left_speed} Motor right:{self.asserv.motor_right_speed}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == 'quit':
            self.exit()
        elif event.button.id == 'emergency_stop':
            self.asserv.emergency_stop()
        elif event.button.id == 'reset_stop':
            self.asserv.emergency_reset()
        elif event.button.id == 'low_speed':
            self.asserv.enable_low_speed(True)
        elif event.button.id == 'normal_speed':
            self.asserv.enable_low_speed(False)
        elif event.button.id == 'go':
            dist = self.query_one("#go_dist").value
            if (is_float(dist)):
                self.asserv.go(int(dist))
            else:
                self.notify("Une distance pour le Go non ?", severity="error", timeout=5)
        elif event.button.id == 'turn':
            angle = self.query_one("#turn_degree").value
            if (is_float(angle)):
                self.asserv.turn(int(angle))
            else:
                self.notify("Et l'angle ?", severity="error", timeout=5)
        elif event.button.id == 'goto':
            x = self.query_one("#goto_x").value
            y = self.query_one("#goto_y").value
            if (is_float(x) and is_float(y)):
                self.asserv.go_to(Position(int(x), int(y)))
            else:
                self.notify("Ton point de consigne c'est dla merde!", severity="error", timeout=5)
        elif event.button.id == 'gotoback':
            x = self.query_one("#gotoback_x").value
            y = self.query_one("#gotoback_y").value
            if (is_float(x) and is_float(y)):
                self.asserv.go_to_reverse(Position(int(x), int(y)))
            else:
                self.notify("Ton point de consigne c'est dla merde!", severity="error", timeout=5)
        elif event.button.id == 'face':
            x = self.query_one("#face_x").value
            y = self.query_one("#face_y").value
            if (is_float(x) and is_float(y)):
                self.asserv.face(Position(int(x), int(y)))
            else:
                self.notify("Face de con !", severity="error", timeout=5)
        elif event.button.id == 'orbital':
            angle = self.query_one("#orbital_angle").value
            fw = self.query_one("#orbital_fw").value
            right = self.query_one("#orbital_right").value

            if (is_float(angle)):
                self.asserv.orbital_turn(float(angle), bool(fw), bool(right))
            else:
                self.notify("Et l'angle je l'invente?", severity="error", timeout=5)

        elif event.button.id == 'gotonostop':
            x = self.query_one("#gotonostop_x").value
            y = self.query_one("#gotonostop_y").value
            if (is_float(x) and is_float(y)):
                self.queueNoStopMsg.append(Position(int(x), int(y)))
                self.query_one("#nb_nostop_queued").update(f"Nombre de commande NoStop en file: {len(self.queueNoStopMsg)}")
            else:
                self.notify("Ton X/Y nostop c'est dla marde!", severity="error", timeout=5)

        elif event.button.id == 'nostopsend':
            for position in self.queueNoStopMsg:
                self.asserv.go_to_chain(position)

            self.queueNoStopMsg = []
            self.query_one("#nb_nostop_queued").update(f"Nombre de commande NoStop en file: {len(self.queueNoStopMsg)}")

        self.query_one("#current_id").update(f"Cmd ID courante : {self.asserv.last_sent_command_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a year.")
    parser.add_argument("year", type=int, help="Year in integer format")
    parser.add_argument("robot", type=str, help="Robot type from Robot enum")
    args = parser.parse_args()

    # set logger level
    logging.getLogger('').setLevel(logging.getLevelNamesMapping()['DEBUG'])
    # create file handler which logs even debug messages
    file_handler = logging.handlers.RotatingFileHandler(filename='logs/log.log', backupCount=50)
    file_handler.doRollover()
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    # add the handlers to the logger
    logging.getLogger().addHandler(file_handler)
    logger = logging.getLogger(__name__)
    logger.info("Init logger")

    robot = Robot(args.robot)

    with open(f'config/{args.year}/{robot.value}/config.json') as config_file:
        config_data = json.load(config_file)
        config_file.close()
        app = AsservUi(config_data=config_data)
        app.run()