import logging
from typing import Optional
import cv2

from ia.actions.abstract_action import AbstractAction
from ia.api.camera import Camera

YELLOW_NUT_MARKER_ID = 47
BLUE_NUT_MARKER_ID = 36

class ActionCameraDetectNuts(AbstractAction):
    """
    Class to represent a detection action for nuts using the camera.

    This action captures an image and processes it to detect the nuts. 
    It raises flags depending on which nut crates must be rotated.

    IMPORTANT: This action requires the camera to be initialized beforehand.
    """

    def __init__(self, camera: Camera, flags: set[str] = set(), color: str = "any") -> None:
        """
        Initialize the ActionCameraDetectNuts with optional flags and color.

        :param flags: Optional flags to help in the decision process.
        :param color: The color of nuts to detect ("yellow", "blue", or "any").
        """
        self.logger = logging.getLogger(__name__)
        self.flags = flags
        self.camera = camera
        self.is_finished = False
        self.color = color
        self.rotations = None # None of tuple(bool,bool,bool,bool) for (rotate1, rotate2, rotate3, rotate4)

    def execute(self) -> None:
        """
        Execute the camera detection action by capturing an image and detecting nuts.
        """
        # Capture an image from the camera
        image = self.camera.capture_image()
        # Process the image to detect the nuts
        detected_nuts = self.__detect_nuts(image)
        self.logger.info(f"Detected nuts: {detected_nuts}")
        self.rotations = self.__compute_rotations(detected_nuts)
        self.is_finished = True

    def finished(self) -> bool:
        """
        Check if the action has finished executing.

        :return: True if the action has finished executing, False otherwise.
        """
        return self.is_finished

    def stop(self) -> None:
        """
        Stop the action if it is currently running.
        """
        # TODO: for now, you just cannot stop this action
        pass

    def reset(self) -> None:
        """
        Reset the action so it can be re-executed with execute().
        """
        self.is_finished = False

    def get_flags(self) -> set[str]:
        """
        Retrieve the flags associated with this action.

        In the case of this action, the following flags will be 
        returned when the action is finished:
            - rotateNut1: True if the first nut crate must be rotated, False otherwise
            - rotateNut2: True if the second nut crate must be rotated, False otherwise
            - rotateNut3: True if the third nut crate must be rotated, False otherwise
            - rotateNut4: True if the fourth nut crate must be rotated, False otherwise
        
        :return: The flags associated with this action, or None if no flags are set.
        """
        if not self.is_finished:
            return self.flags
        else:
            rotate1, rotate2, rotate3, rotate4 = self.rotations
            if rotate1:
                self.flags.add("rotateNut1")
            if rotate2:
                self.flags.add("rotateNut2")
            if rotate3:
                self.flags.add("rotateNut3")
            if rotate4:
                self.flags.add("rotateNut4")
            return self.flags
        
    def __detect_nuts(self, image) -> list[str]:
        """
        Internal method to process the captured image and detect the nuts.

        :param image: The captured image (RGB) from the camera.

        :return: A list of detected nuts, sorted from left to right (e.g., ["yellow", "blue", "yellow", "yellow"]).
        """
        # Convert the image to grayscale for processing
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Select the correct arUco markers to find
        aruco_dict = cv2.aruco.getPredefinedDictionary(
            cv2.aruco.DICT_4X4_100
        )
        aruco_params = cv2.aruco.DetectorParameters()

        # Detect the markers in the image
        corners, ids, rejected = cv2.aruco.detectMarkers(gray, aruco_dict)

        # Filter out the detected markers to find the ones corresponding to the nuts
        nuts = [] # List of tuples (marker_id, corners) for the detected nuts
        if ids is not None:
            for i, marker_id in enumerate(ids.flatten()):
                pts = corners[i][0]  # 4 corner points (x, y)

                if marker_id == YELLOW_NUT_MARKER_ID:
                    nuts.append(("yellow", pts))
                elif marker_id == BLUE_NUT_MARKER_ID:
                    nuts.append(("blue", pts))
        
        # Sort the nuts (left most first) 
        def most_left_point(crate):
            corners = crate[1]
            min_x = corners[0][0]
            for corner in corners:
                if corner[0] < min_x:
                    min_x = corner[0]
            return min_x
        nuts.sort(key=most_left_point, reverse=False)

        # TODO: ROI?

        return list(map(lambda n: n[0], nuts))
    
    def __compute_rotations(self, detected_nuts: list[str]) -> tuple[bool,bool,bool,bool]:
        """
        Internal method to compute the rotations to apply to the nut crates based on the detected nuts.

        :param detected_nuts: A list of detected nuts, sorted from left to right (e.g., ["yellow", "blue", "yellow", "yellow"]).

        :return: A tuple of booleans indicating whether to rotate each nut crate (rotate1, rotate2, rotate3, rotate4).
        """
        if len(detected_nuts) != 4:
            self.logger.warning(f"Expected to detect 4 nuts, but detected {len(detected_nuts)}. Detected nuts: {detected_nuts}")
            return (False, False, False, False)
        if self.color == "yellow":
            # Rotate the crates that do not contain yellow nuts
            return tuple(nut != "yellow" for nut in detected_nuts)
        elif self.color == "blue":
            # Rotate the crates that do not contain blue nuts
            return tuple(nut != "blue" for nut in detected_nuts)
        else: # self.color == "any"
            # Just detect the nuts without rotating any crate
            return (False, False, False, False)
        

class ActionBlueCameraDetectNuts(ActionCameraDetectNuts):
    """
    Class to represent a nut detection action for blue team using the camera.

    This action captures an image and processes it to detect the other team's nuts. 
    It raises flags depending on which nut crates must be rotated.

    IMPORTANT: This action requires the camera to be initialized beforehand.
    """

    def __init__(self, camera: Camera, flags: dict[str, bool] = {}) -> None:
        """
        Initialize the ActionBlueCameraDetectNuts with optional flags.

        :param flags: Optional flags to help in the decision process.
        """
        super().__init__(camera, flags, color="blue")

class ActionYellowCameraDetectNuts(ActionCameraDetectNuts):
    """
    Class to represent a nut detection action for yellow team using the camera.

    This action captures an image and processes it to detect the other team's nuts. 
    It raises flags depending on which nut crates must be rotated.

    IMPORTANT: This action requires the camera to be initialized beforehand.
    """

    def __init__(self, camera: Camera, flags: set[str] = set()) -> None:
        """
        Initialize the ActionYellowCameraDetectNuts with optional flags.

        :param flags: Optional flags to help in the decision process.
        """
        super().__init__(camera, flags, color="yellow")