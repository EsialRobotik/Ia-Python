import logging

import cbor2
import crc

from ia.asservissement.asser_message import AsservMessage
from ia.asservissement.asserv_response_listener import AsservResponseListener
from ia.asservissement.asserv_status import AsservStatus
from ia.asservissement.movement_direction import MovementDirection
from ia.utils.position import Position

logger = logging.getLogger(__name__)

import serial
import threading
import time

class Asserv:
    """
    The Asserv class provides an interface to control a robot's movement and position using a serial connection.
    Attributes:
        serial_port (str): The serial port to which the robot is connected.
        baud_rate (int): The baud rate for the serial communication.
        serial (serial.Serial): The serial connection object.
        position (position): The current position of the robot.
        direction (movement_direction): The current movement direction of the robot.
        status_countdown (int): Countdown for the status of the robot.
        asserv_status (asserv_status): The current status of the robot.
        queue_size (int): The size of the command queue.
        gostart_config (dict): Configuration for the go start sequence.
        lock (threading.Lock): A lock to ensure thread safety.
        read_thread (threading.Thread): A thread to read and parse the robot's position.
    Methods:
        initialize(): Initializes the robot.
        stop(): Stops the robot.
        emergency_stop(): Performs an emergency stop.
        emergency_reset(): Resets the robot after an emergency stop.
        go(dist): Moves the robot forward or backward by a specified distance.
        turn(degree): Turns the robot by a specified degree.
        go_to(position): Moves the robot to a specified position.
        go_to_chain(position): Moves the robot to a specified position in a chain of movements.
        go_to_reverse(position): Moves the robot to a specified position in reverse.
        face(position): Faces the robot towards a specified position.
        set_odometrie(x, y, theta): Sets the odometry of the robot.
        enable_low_speed(enable): Enables or disables low speed mode.
        set_speed(pct): Sets the speed of the robot as a percentage.
        set_speed_callage(pct): Sets the speed of the robot for callage.
        enable_regulator_angle(enable): Enables or disables the angle regulator.
        reset_regulator_angle(): Resets the angle regulator.
        enable_regulator_distance(enable): Enables or disables the distance regulator.
        reset_regulator_distance(): Resets the distance regulator.
        enable_motors(enable): Enables or disables the motors.
        parse_asserv_position(str): Parses the position data from the robot.
        wait_for_asserv(): Waits for the robot to finish its current command.
        wait_for_halted_or_blocked(timeout_ms): Waits for the robot to be halted or blocked within a timeout.
        go_start(is_color0): Executes the go start sequence based on the color configuration.
    """

    def __init__(self, serial_port: str, baud_rate: int, gostart_config: dict) -> None:
        """
        Initializes the Asserv object with the given serial port, baud rate, and gostart configuration.
        Args:
            serial_port (str): The serial port to be used for communication.
            baud_rate (int): The baud rate for the serial communication.
            gostart_config (dict): Configuration settings for the gostart.
        Attributes:
            serial_port (str): The serial port to be used for communication.
            baud_rate (int): The baud rate for the serial communication.
            serial (serial.Serial): The serial communication object.
            position (position): The current position of the robot.
            direction (None): The current direction of the robot (initially None).
            status_countdown (int): Countdown for the status (initially 0).
            asserv_status (asserv_status): The current status of the asservissement (initially STATUS_IDLE).
            queue_size (int): The size of the command queue (initially 0).
            gostart_config (dict): Configuration settings for the gostart.
            lock (threading.Lock): A lock for thread-safe operations.
            read_thread (threading.Thread): A thread for reading and parsing the asservissement position.
        """

        self.serial_port = serial_port
        self.baud_rate = baud_rate
        logger.info(f"Creating Asserv object with serial port {serial_port} and baud rate {baud_rate}.")
        self.serial = serial.Serial(
            port=serial_port,
            baudrate=baud_rate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.01
        )
        self.position = Position(0, 0)
        self.last_log = ''
        self.direction = None
        self.status_countdown = 0
        self.asserv_status = AsservStatus.STATUS_IDLE
        self.queue_size = 0
        self.last_sent_command_id = 0
        self.last_received_command_id = 0
        self.motor_left_speed = 0
        self.motor_right_speed = 0
        self.gostart_config = gostart_config
        self.reading_buffer = []
        self.lock = threading.Lock()
        self.response_listener = AsservResponseListener()
        self.serial.read()
        logger.info('Start asser reading thread')
        self.read_thread = threading.Thread(target=self.parse_asserv_position)
        self.read_thread.daemon = True
        self.read_thread.start()
        logger.info('Start asserv update_position thread')
        self.update_position_thread = threading.Thread(target=self._update_position_loop)
        self.update_position_thread.daemon = True
        self.update_position_thread.start()

    def get_next_command_id(self) -> int:
        self.last_sent_command_id += 1
        return self.last_sent_command_id

    def formatMsg(self, msg):
        """
        Format cbor message to send order
        """
        syncword = 0xDEADBEEF
        msg_cbor = cbor2.dumps(msg)
        msg_cbor_len = len(msg_cbor)
        calculator = crc.Calculator(crc.Crc32.CRC32)
        crc_computed = calculator.checksum(msg_cbor)
        logger.info(f'Forge message {msg}')
        return (syncword.to_bytes(length=4, byteorder='little', signed=False)
            + crc_computed.to_bytes(length=4, byteorder='little', signed=False)
            + msg_cbor_len.to_bytes(length=4, byteorder='little', signed=False)
            + msg_cbor)

    def emergency_stop(self) -> None:
        """
        Immediately halts the robot's movement and updates its status.
        This method performs the following actions:
        - Logs an "emergencyStop" message.
        - Sets the robot's status to `STATUS_HALTED`.
        - Sends a halt command ("h") to the robot's serial interface.
        - Sets the movement direction to `NONE`.
        This method is typically used in emergency situations where the robot needs to stop all operations immediately.
        """

        logger.info("emergencyStop")
        self.asserv_status = AsservStatus.STATUS_HALTED
        self.serial.write(self.formatMsg({"cmd": AsservMessage.emergency_stop.value}))
        self.direction = MovementDirection.NONE

    def emergency_reset(self) -> None:
        """
        Resets the system to an idle state in case of an emergency.
        This method logs an emergency reset event, sets the asserv_status to 
        STATUS_IDLE, and sends a reset command ('r') via the serial interface.
        """

        logger.info("emergencyReset")
        self.asserv_status = AsservStatus.STATUS_IDLE
        self.serial.write(self.formatMsg({"cmd": AsservMessage.emergency_stop_reset.value}))

    def go(self, dist: int) -> None:
        """
        Initiates movement of the robot for a specified distance.
        Args:
            dist (int): The distance to move. Positive values indicate forward movement,
                          while negative values indicate backward movement.
        Raises:
            None
        Side Effects:
            - Logs the movement command.
            - Updates the asserv_status to STATUS_RUNNING.
            - Sets the status_countdown to 2 within a thread-safe block.
            - Sets the movement direction based on the distance.
            - Sends the movement command to the serial interface.
        """

        logger.info(f"go : {dist}")
        self.asserv_status = AsservStatus.STATUS_RUNNING
        with self.lock:
            self.status_countdown = 2
        self.direction = MovementDirection.FORWARD if dist > 0 else MovementDirection.BACKWARD
        self.serial.write(self.formatMsg({
            "cmd": AsservMessage.straight.value,
            "D" : float(dist),
            "ID": self.get_next_command_id()
        }))

    def turn(self, degree: int) -> None:
        """
        Rotates the robot by a specified degree.
        Args:
            degree (int): The degree to turn the robot. Positive values indicate a clockwise turn, 
                  while negative values indicate a counterclockwise turn.
        Logs:
            Logs the turn action with the specified degree.
        Updates:
            - Sets the asserv_status to STATUS_RUNNING.
            - Sets the status_countdown to 2 within a thread-safe block.
            - Sets the direction to MovementDirection.NONE.
            - Sends the turn command to the robot's serial interface.
        """

        logger.info(f"turn : {degree}")
        self.asserv_status = AsservStatus.STATUS_RUNNING
        with self.lock:
            self.status_countdown = 2
        self.direction = MovementDirection.NONE
        self.serial.write(self.formatMsg({
            "cmd": AsservMessage.turn.value,
            "A": float(degree),
            "ID": self.get_next_command_id()
        }))

    def go_to(self, position: Position) -> None:
        """
        Moves the robot to the specified position.
        Args:
            position (position): The target position to move to, containing x and y coordinates.
        Logs:
            Logs the target position using the logger.
        Updates:
            - Sets the asserv_status to STATUS_RUNNING.
            - Sets the status_countdown to 2 within a thread-safe block.
            - Sets the movement direction to FORWARD.
            - Sends the target position to the robot via serial communication.
        """

        logger.info(f"goTo : {position}")
        self.asserv_status = AsservStatus.STATUS_RUNNING
        with self.lock:
            self.status_countdown = 2
        self.direction = MovementDirection.FORWARD
        self.serial.write(self.formatMsg({
            "cmd": AsservMessage.goto_front.value,
            "X" : float(position.x),
            "Y" : float(position.y),
            "ID": self.get_next_command_id()
        }))

    def go_to_chain(self, position: Position) -> None:
        """
        Moves the robot to the specified position and a chain of movements.
        Args:
            position (position): The target position to move to, containing x and y coordinates.
        Logs:
            Logs the target position using the logger.
        Side Effects:
            - Sets the asserv_status to STATUS_RUNNING.
            - Sets the status_countdown to 2 within a thread-safe block.
            - Sets the movement direction to FORWARD.
            - Sends the target position to the serial interface in the format "e{x}#{y}".
        """

        logger.info(f"goToChain : {position}")
        self.asserv_status = AsservStatus.STATUS_RUNNING
        with self.lock:
            self.status_countdown = 2
        self.direction = MovementDirection.FORWARD
        self.serial.write(self.formatMsg({
            "cmd": AsservMessage.goto_nostop.value,
            "X": float(position.x),
            "Y": float(position.y),
            "ID": self.get_next_command_id()
        }))

    def go_to_reverse(self, position: Position) -> None:
        """
        Initiates a reverse movement to the specified position.
        Args:
            position (position): The target position to move to in reverse. 
                                 It should have 'x' and 'y' attributes representing coordinates.
        Logs:
            Logs the action with the target position.
        Updates:
            - Sets the asserv_status to STATUS_RUNNING.
            - Sets the status_countdown to 2 within a thread-safe block.
            - Sets the movement direction to BACKWARD.
            - Sends the target position to the serial interface in the format "b{x}#{y}".
        """

        logger.info(f"goToReverse : {position}")
        self.asserv_status = AsservStatus.STATUS_RUNNING
        with self.lock:
            self.status_countdown = 2
        self.direction = MovementDirection.BACKWARD
        self.serial.write(self.formatMsg({
            "cmd": AsservMessage.goto_back.value,
            "X": float(position.x),
            "Y": float(position.y),
            "ID": self.get_next_command_id()
        }))

    def face(self, position: Position) -> None:
        """
        Directs the robot to face a given position.
        Args:
            position (position): The target position with x and y coordinates.
        Raises:
            Exception: If there is an issue with serial communication.
        Logs:
            Logs the target position using the logger.
        """

        logger.info(f"goToFace : {position}")
        self.asserv_status = AsservStatus.STATUS_RUNNING
        with self.lock:
            self.status_countdown = 2
        self.direction = MovementDirection.NONE
        self.serial.write(self.formatMsg({
            "cmd": AsservMessage.face.value,
            "X": float(position.x),
            "Y": float(position.y),
            "ID": self.get_next_command_id()
        }))

    def orbital_turn(self, degrees : float, forward : bool, turn_right : bool):
        logger.info(f"orbitalTurn : {degrees} - {forward} - {turn_right}")
        self.asserv_status = AsservStatus.STATUS_RUNNING
        with self.lock:
            self.status_countdown = 2
        self.direction = MovementDirection.FORWARD
        self.serial.write(self.formatMsg({
            "cmd": AsservMessage.orbital_turn.value,
            "A" : float(degrees),
            "F" : float(1.0) if forward else float(0),
            "R" : float(1.0) if turn_right else float(0),
            "ID": self.get_next_command_id()
        }))

    def set_odometrie(self, x: int, y: int, theta: float) -> None:
        """
        Sets the odometry values for the robot.
        Parameters:
        x (float): The x-coordinate of the robot's position.
        y (float): The y-coordinate of the robot's position.
        theta (float): The orientation angle of the robot in radians.
        Returns:
        None
        """

        logger.info(f"setOdometrie P{x}#{y}#{theta}")
        self.serial.write(self.formatMsg({
            "cmd": AsservMessage.set_position.value,
            "X" : float(x),
            "Y" : float(y),
            "T" : float(theta)
        }))

    def enable_low_speed(self, enable: bool) -> None:
        """
        Enables or disables low speed mode for the robot.
        Parameters:
        enable (bool): If True, low speed mode is enabled. If False, low speed mode is disabled.
        Returns:
        None
        """

        logger.info(f"enableLowSpeed : {enable}")
        if enable:
            self.serial.write(self.formatMsg({"cmd": AsservMessage.slow_speed_acc_mode.value}))
        else:
            self.serial.write(self.formatMsg({"cmd": AsservMessage.normal_speed_acc_mode.value}))

    def set_speed(self, pct: int) -> None:
        """
        Set the speed of the robot.
        This method sets the speed of the robot to the specified percentage.
        It also enables or disables low speed mode based on whether the 
        percentage is 100 or not.
        Args:
            pct (int): The speed percentage to set. Should be between 0 and 100.
        Returns:
            None
        """

        logger.info(f"setSpeed {pct}%")
        self.enable_low_speed(pct != 100)

    def set_speed_callage(self, pct: int) -> None:
        """
        Set the speed of the robot by sending a command to the serial interface.
        Parameters:
        pct (int): The speed percentage to set. This should be an integer value representing the desired speed as a percentage.
        Returns:
        None
        """

        logger.info(f"setSpeed {pct}%")
        self.serial.write(self.formatMsg({
            "cmd": AsservMessage.max_motor_speed.value,
            "P" : float(pct),
            "ID": int(4242)
        }))

    def parse_asserv_position(self) -> None:
        while True:
            x = self.serial.read(50)
            for val in x:
                self.response_listener.push_byte(val)

    def _update_position_loop(self) -> None:
        while True:
            self.update_position()
            time.sleep(0.001)

    def update_position(self) -> None:
        while self.response_listener.get_nb_payload() > 0 :
            payload = self.response_listener.pop_payload()
            self.last_log = payload
            logger.debug(f"Position : {self.last_log}")
            self.position.x = int(payload['x'])
            self.position.y = int(payload['y'])
            self.position.theta = float(payload['theta'])
            asserv_status_int = int(payload['status'])
            if asserv_status_int == 0:
                with self.lock:
                    self.status_countdown -= 1
                    if self.status_countdown <= 0:
                        self.asserv_status = AsservStatus.STATUS_IDLE
            elif asserv_status_int == 1:
                self.asserv_status = AsservStatus.STATUS_RUNNING
            elif asserv_status_int == 2:
                self.asserv_status = AsservStatus.STATUS_HALTED
            elif asserv_status_int == 3:
                self.asserv_status = AsservStatus.STATUS_BLOCKED
            self.queue_size = int(payload['pending'])
            self.last_received_command_id = int(payload['cmd_id'])
            self.motor_left_speed = int(payload['motor_left'])
            self.motor_right_speed = int(payload['motor_right'])

    def wait_for_asserv(self) -> None:
        """
        Waits for the asservissement process to complete.
        This method continuously checks the status of the asservissement process
        and waits until the queue is empty and the asservissement status is idle. It
        pauses for 5 milliseconds between each check to avoid busy-waiting.
        Returns:
            None
        """

        while not (self.is_last_command_finished()):
            time.sleep(0.005)

    def wait_for_halted_or_blocked(self, timeout_ms: int) -> None:
        """
        Waits for the asservissement system to halt or become blocked within a specified timeout.
        Args:
            timeout_ms (int): The maximum time to wait in milliseconds.
        Returns:
            None
        """

        start_time = time.time_ns()
        while self.asserv_status == AsservStatus.STATUS_RUNNING and ((time.time_ns() - start_time)  / 1000000) < timeout_ms:
            time.sleep(0.01)

    def is_last_command_finished(self) -> bool:
        return (self.last_received_command_id > self.last_sent_command_id or
                (self.last_received_command_id == self.last_sent_command_id
                 and self.asserv_status == AsservStatus.STATUS_IDLE))

    def go_start(self, color: str) -> None:
        """
        Executes a series of movement instructions to start the robot.
        Parameters:
        color (str): Determines the starting configuration based on color
        The method processes a list of instructions, where each instruction is a dictionary 
        containing the type of movement and associated parameters. The supported instruction 
        types are:
        - "go": Move forward a specified distance.
        - "go_timed": Move forward a specified distance with a time limit.
        - "turn": Turn by a specified distance.
        - "goto": Move to a specified (x, y) position.
        - "goto_back": Move to a specified (x, y) position in reverse.
        - "face": Face towards a specified (x, y) position.
        - "angle": Enable or disable the angle regulator.
        - "distance": Enable or disable the distance regulator.
        - "set_x": Set the odometry X value.
        - "set_y": Set the odometry Y value.
        - "speed": Set the movement speed.
        Raises:
        Exception: If an unknown instruction type is encountered.
        The method also logs each instruction and its execution status.
        """

        start = self.gostart_config[color]
        time.sleep(0.15)
        for instruction in start:
            temp = instruction
            logger.debug(temp)
            if temp["type"] == "go":
                self.go(temp["dist"])
                logger.info(f"Go {temp['dist']}")
            elif temp["type"] == "go_timed":
                logger.info(f"Go timed {temp['dist']}")
                self.go(temp["dist"])
                self.wait_for_halted_or_blocked(500)
                self.emergency_stop()
                time.sleep(2)
                self.emergency_reset()
                logger.info(f"Go timed end {temp['dist']}")
            elif temp["type"] == "turn":
                self.turn(temp["dist"])
                logger.info(f"Turn {temp['dist']}")
            elif temp["type"] == "goto":
                depart = Position(temp["x"], temp["y"])
                logger.info(f"Goto {depart}")
                self.go_to(depart)
            elif temp["type"] == "goto_back":
                depart = Position(temp["x"], temp["y"])
                logger.info(f"Goto {depart}")
                self.go_to_reverse(depart)
            elif temp["type"] == "face":
                alignement = Position(temp["x"], temp["y"])
                logger.info(f"Goto {alignement}")
                self.face(alignement)
            elif temp["type"] == "set_x":
                logger.info(f"Set odometrie X : {temp['value']}")
                self.set_odometrie(temp["value"], self.position.y, temp["theta"])
            elif temp["type"] == "set_y":
                logger.info(f"Set odometrie Y : {temp['value']}")
                self.set_odometrie(self.position.x, temp["value"], temp["theta"])
            elif temp["type"] == "speed":
                logger.info(f"Set speed {temp['value']}")
                self.set_speed_callage(temp["value"])
            else:
                raise Exception(f"Unknown instruction {temp}")
            self.wait_for_asserv()
        time.sleep(0.15)
        logger.info("goStart finished")