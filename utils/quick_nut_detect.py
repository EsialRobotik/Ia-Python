import time
import datetime
import cv2
import numpy as np
from picamera2 import Picamera2

"""
Quick script to test the nut detection without running the whole IA (also because I don't 
know how to make it run without breaking something else). 
It works perfectly on the "test" Raspberry Pi 3B.
"""

YELLOW_NUT_MARKER_ID = 47
BLUE_NUT_MARKER_ID = 36
TEAMCOLOR = "yellow" # "yellow" or "blue"

def capture_image(picam2):
    #print("start", datetime.datetime.now())
    image = picam2.capture_array("main")
    #print("end", datetime.datetime.now())

    return image

def open_image(path):
    image = cv2.imread(path)
    if image is None:
        raise FileNotFoundError(f"Image not found at path: {path}")
    return image

def detect_nuts(image) -> list[str]:
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

def compute_rotations(detected_nuts: list[str]) -> tuple[bool,bool,bool,bool]:
    """
    Internal method to compute the rotations to apply to the nut crates based on the detected nuts.
    :param detected_nuts: A list of detected nuts, sorted from left to right (e.g., ["yellow", "blue", "yellow", "yellow"]).
    :return: A tuple of booleans indicating whether to rotate each nut crate (rotate1, rotate2, rotate3, rotate4).
    """
    if len(detected_nuts) != 4:
        return (False, False, False, False)
    if TEAMCOLOR == "yellow":
        # Rotate the crates that do not contain yellow nuts
        return tuple(nut != "yellow" for nut in detected_nuts)
    elif TEAMCOLOR == "blue":
        # Rotate the crates that do not contain blue nuts
        return tuple(nut != "blue" for nut in detected_nuts)
    else: # self.color == "any"
        # Just detect the nuts without rotating any crate
        return (False, False, False, False)

def main():
    picam2 = Picamera2()

    # Configure camera for still capture
    config = picam2.create_still_configuration(
        main={"size": (1280, 720), "format": "RGB888"}
    )
    picam2.configure(config)

    picam2.start(show_preview=False)
    time.sleep(1)  # Allow auto-exposure to settle

    #image = open_image("test4.jpg")
    while True:
        image = capture_image(picam2)
        detected_nuts = detect_nuts(image)

        if not detected_nuts:
            print("No nuts detected.")
            continue

        print(f"Detected nuts: {detected_nuts}")
        rotate1, rotate2, rotate3, rotate4 = compute_rotations(detected_nuts)
        print(f"Rotate crates: {rotate1}, {rotate2}, {rotate3}, {rotate4}")

if __name__ == "__main__":
    main()
