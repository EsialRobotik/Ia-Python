import logging
logger = logging.getLogger(__name__)

import serial
from time import sleep
import threading

class NextionNX32224T024:
    """
    A class to interface with the Nextion NX32224T024 display module.
    Attributes:
        status (str): The status message to be displayed.
        color (str): The current color displayed.
        calibrationStarted (bool): Flag to indicate if calibration has started.
        color0 (str): The initial color to be compared against.
        serial (serial.Serial): The serial connection to the Nextion display.
        read_thread (threading.Thread): The thread for reading serial data.
    Methods:
        send_instruction(instruction):
            Sends an instruction to the Nextion display.
        goto_page(page_name):
            Navigates to a specified page on the Nextion display.
        display_color(color):
            Displays the specified color on the Nextion display.
        display_calibration_status(status):
            Displays the calibration status on the Nextion display.
        display_score(score):
            Displays the score on the Nextion display.
        parse_line(line):
            Parses a line of input from the serial connection and performs the corresponding action.
        is_color0():
            Checks if the current color matches the initial color.
        wait_for_calibration():
            Waits until calibration has started.
        read_serial():
            Continuously reads from the serial connection and processes incoming data.
    """


    def __init__(self, serialPort, baudRate, color0):
        """
        Initializes the NextionNX32224T024 object.
        Args:
            serialPort (str): The serial port to which the Nextion display is connected.
            baudRate (int): The baud rate for the serial communication.
            color0 (str): The name for color0.
        Attributes:
            status (str): The status of the display.
            color (str): The current color setting of the display.
            calibrationStarted (bool): Indicates if the calibration process has started.
            color0 (str): The name for color0.
            serial (serial.Serial): The serial connection to the Nextion display.
            read_thread (threading.Thread): The thread responsible for reading data from the serial port.
        """

        logger.info(f"Creating NextionNX32224T024 object with serial port {serialPort} and baud rate {baudRate}.")
        self.status = ""
        self.color = ""
        self.calibrationStarted = False
        self.color0 = color0
        self.serial = serial.Serial(
            port=serialPort,
            baudrate=baudRate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
        self.read_thread = threading.Thread(target=self.read_serial)
        self.read_thread.daemon = True
        self.read_thread.start()

    def send_instruction(self, instruction):
        """
        Sends an instruction to the Nextion display.
        This method encodes the given instruction as an ASCII string and appends
        the required end-of-command bytes (0xFF 0xFF 0xFF) before writing it to
        the serial port.
        Args:
            instruction (str): The instruction to send to the Nextion display.
        """

        logger.info(f"Sending instruction: {instruction}")
        self.serial.write(instruction.encode('ascii') + b'\xff\xff\xff')

    def goto_page(self, page_name):
        """
        Navigate to a specific page on the Nextion display.
        Parameters:
        page_name (str): The name of the page to navigate to. 
                 Valid values are "init", "color", "calibration", "ready", and "score".
        Raises:
        ValueError: If an invalid page_name is provided.
        Example:
        >>> goto_page("init")
        This will navigate to the "page0" on the Nextion display.
        """

        page = "unknow"
        if page_name == "init":
            page = "page0"
        elif page_name == "color":
            page = "page1"
        elif page_name == "calibration":
            page = "page2"
        elif page_name == "ready":
            page = "page3"
        elif page_name == "score":
            page = "page4"
        self.send_instruction(f"page {page}")

    def display_color(self, color):
        """
        Updates the display with the specified color.
        Args:
            color (str): The color to be displayed. It should be a string representing the color name or code.
        """

        self.send_instruction(f"robotcolor.txt=\"{color.upper()}\"")

    def display_calibration_status(self, status):
        """
        Updates the display with the current calibration status.
        Args:
            status (str): The current status message to be appended and displayed.
        """

        self.status += "\r\n"+status
        self.send_instruction(f"status.txt=\"{self.status}\"")

    def display_score(self, score):
        """
        Updates the display to show the given score.
        Args:
            score (int): The score to be displayed on the screen.
        """

        self.send_instruction(f"score.val={score}")

    def parse_line(self, line):
        """
        Parses a given line of text and performs actions based on its content.
        Args:
            line (str): The line of text to parse.
        Actions:
            - If the line starts with "gopage", it extracts the page name and navigates to that page.
              If the page is "calibration", it updates the display with the calibration status and sets
              the calibrationStarted flag to True.
            - If the line starts with "color", it extracts the color value and updates the display and
              the internal color attribute with the new color value.
        """

        logger.info(f"Parsing line: {line}")
        if line.startswith("gopage"):
            page = line.split(" ")[1]
            self.goto_page(page)
            if page == "calibration":
                self.display_calibration_status("Debut calibration")
                self.calibrationStarted = True
        elif line.startswith("color"):
            self.display_color(line.split(" ")[1])
            self.color = line.split(" ")[1]

    def is_color0(self):
        """
        Check if the current color is equal to color0.
        Returns:
            bool: True if the current color is equal to color0, False otherwise.
        """

        return self.color == self.color0
    
    def wait_for_calibration(self):
        """
        Waits for the calibration process to start.
        This method enters an infinite loop, checking every 0.05 seconds if the 
        calibration process has started. Once the calibration process starts, 
        the method returns and exits the loop.
        Returns:
            None
        """

        logger.info("Waiting for calibration to start.")
        while True:
            sleep(0.05)
            if self.calibrationStarted:
                return
            
    def read_serial(self):
        """
        Continuously reads data from the serial port.
        This method runs an infinite loop that checks if there is any data waiting
        in the serial buffer. If data is available, it reads a line from the serial
        port, decodes it from ASCII, strips any leading/trailing whitespace, and
        passes the resulting string to the `parse_line` method for further processing.
        Note:
            This method will block indefinitely. Ensure that it is run in a separate
            thread or process if you need your program to perform other tasks concurrently.
        Raises:
            SerialException: If there is an issue with the serial connection.
        """

        while True:
            if self.serial.in_waiting > 0:
                line = self.serial.readline().decode('ascii').strip()
                self.parse_line(line)