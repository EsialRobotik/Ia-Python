import logging
import threading
import time

from gpiozero import DistanceSensor

from ia.api.detection.ultrasound.srf import Srf

logger = logging.getLogger(__name__)

class Srf04(Srf):
    """
    A class to represent an SRF04 ultrasonic sensor.
    Attributes
    ----------
    trigger : int
        GPIO pin number for the trigger.
    echo : int
        GPIO pin number for the echo.
    sensor : DistanceSensor
        Instance of the DistanceSensor class.
    x : int
        X-coordinate of the sensor's position.
    y : int
        Y-coordinate of the sensor's position.
    angle : int
        Orientation angle of the sensor.
    threshold : int
        Distance threshold for the sensor.
    Methods
    -------
    get_position():
        Returns the position of the sensor as a Position object.
    get_threshold():
        Returns the distance threshold of the sensor.
    get_distance():
        Returns the measured distance from the sensor in milimeters.
    """

    POLL_INTERVAL_S = 0.02
    STALE_THRESHOLD_S = 0.5


    def __init__(self, desc: str, trigger: int, echo: int, x: int, y: int, angle: int, threshold: int, window_size: int) -> None:
        """
        Initializes the Srf04 sensor with the given parameters.
        Args:
            trigger (int): GPIO pin number for the trigger.
            echo (int): GPIO pin number for the echo.
            x (int): X-coordinate of the sensor's position.
            y (int): Y-coordinate of the sensor's position.
            angle (int): Angle at which the sensor is mounted.
            threshold (int): Distance threshold for detection.
        """

        super().__init__(desc, x, y, angle, threshold, window_size)
        logger.info(f"Creating Srf04 object with trigger {trigger}, echo {echo}, x {x}, y {y}, angle {angle}, threshold {threshold}.")
        self.sensor = DistanceSensor(
            echo=echo,
            trigger=trigger,
            queue_len= self.window_size
        )
        self._last_distance: int = 10000
        self._last_read_ts: float = 0.0
        self._measure_thread = threading.Thread(target=self._measurement_loop, daemon=True)
        self._measure_thread.start()

    def _measurement_loop(self) -> None:
        while True:
            try:
                value = self.sensor.value
                self._last_distance = 10000 if value == 0 else int(value * 1000)
                self._last_read_ts = time.monotonic()
            except Exception:
                logger.exception(f"SRF04 {self.desc} read failed")
            time.sleep(self.POLL_INTERVAL_S)

    def get_distance(self) -> int:
        """
        Return the last cached distance in millimeters. Reads are produced by a background
        thread so a stuck gpiozero call cannot block the main loop. If no fresh measurement
        has arrived for STALE_THRESHOLD_S, return 10000 (treat as "no obstacle") so the
        match keeps running even if the sensor stops responding.
        """
        if time.monotonic() - self._last_read_ts > self.STALE_THRESHOLD_S:
            return 10000
        return self._last_distance