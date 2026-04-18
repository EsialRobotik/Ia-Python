import logging
from typing import Optional

import cv2

from ia.actions.registry import action_type
from ia.actions.threaded_action import ThreadedAction
from ia.api.camera import Camera


ARUCO_DICTIONARIES = {
    "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
    "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
    "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
    "DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,
    "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
    "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
    "DICT_5X5_250": cv2.aruco.DICT_5X5_250,
    "DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,
    "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
    "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
    "DICT_6X6_250": cv2.aruco.DICT_6X6_250,
    "DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,
}


@action_type("camera_detect_aruco")
class ActionCameraDetectAruco(ThreadedAction):
    """Capture une image, détecte des marqueurs ArUco et lève des flags selon des règles configurables."""

    def __init__(
        self,
        camera: Camera,
        dictionary: str,
        markers: dict[int, str],
        rules: list[dict],
        sort_mode: Optional[str] = None,
        expected_count: Optional[int] = None,
        flags: Optional[list[str]] = None,
    ) -> None:
        super().__init__(flags)
        self.logger = logging.getLogger(__name__)
        self.camera = camera
        self.dictionary_name = dictionary
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICTIONARIES[dictionary])
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.markers = markers  # {marker_id: label}
        self.rules = rules
        self.sort_mode = sort_mode
        self.expected_count = expected_count
        self._raised_flags: list[str] = []

    @classmethod
    def from_json(cls, payload: dict, **deps) -> 'ActionCameraDetectAruco':
        camera = deps.get("camera")
        if camera is None:
            raise ValueError("camera dependency is required for camera_detect_aruco action")
        if "dictionary" not in payload:
            raise ValueError("'dictionary' missing in camera_detect_aruco payload")
        if payload["dictionary"] not in ARUCO_DICTIONARIES:
            raise ValueError(f"Unknown ArUco dictionary: {payload['dictionary']}")
        if "markers" not in payload:
            raise ValueError("'markers' missing in camera_detect_aruco payload")
        markers = {int(k): v for k, v in payload["markers"].items()}
        return cls(
            camera=camera,
            dictionary=payload["dictionary"],
            markers=markers,
            rules=payload.get("rules", []),
            sort_mode=payload.get("sort"),
            expected_count=payload.get("expected_count"),
            flags=payload.get("flags"),
        )

    def reset(self) -> None:
        super().reset()
        self._raised_flags = []

    def get_flags(self) -> Optional[list[str]]:
        base = list(self.flags) if self.flags else []
        combined = base + self._raised_flags
        return combined if combined else None

    def _run(self) -> None:
        image = self.camera.capture_image()
        detections = self._detect(image)
        self.logger.info(f"Detected markers: {[(d['label'], d['id']) for d in detections]}")
        if self.expected_count is not None and len(detections) != self.expected_count:
            self.logger.warning(
                f"Expected {self.expected_count} markers, detected {len(detections)} — rules skipped"
            )
            self._finished = True
            return
        for rule in self.rules:
            self._apply_rule(rule, detections)
        self.logger.info(f"Raised flags: {self._raised_flags}")
        self._finished = True

    def _detect(self, image) -> list[dict]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = cv2.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.aruco_params)
        if ids is None:
            return []
        detections = []
        for i, marker_id in enumerate(ids.flatten()):
            marker_id = int(marker_id)
            if marker_id not in self.markers:
                continue
            detections.append({
                "id": marker_id,
                "label": self.markers[marker_id],
                "corners": corners[i][0],
            })
        return self._sort(detections)

    def _sort(self, detections: list[dict]) -> list[dict]:
        if not self.sort_mode or not detections:
            return detections
        if self.sort_mode == "left_to_right":
            detections.sort(key=lambda d: min(c[0] for c in d["corners"]))
        elif self.sort_mode == "right_to_left":
            detections.sort(key=lambda d: min(c[0] for c in d["corners"]), reverse=True)
        elif self.sort_mode == "top_to_bottom":
            detections.sort(key=lambda d: min(c[1] for c in d["corners"]))
        elif self.sort_mode == "bottom_to_top":
            detections.sort(key=lambda d: min(c[1] for c in d["corners"]), reverse=True)
        else:
            self.logger.warning(f"Unknown sort mode: {self.sort_mode}")
        return detections

    def _apply_rule(self, rule: dict, detections: list[dict]) -> None:
        rule_type = rule.get("type")
        if rule_type == "positional_label_mismatch":
            self._rule_positional_mismatch(rule, detections)
        elif rule_type == "label_present":
            self._rule_label_present(rule, detections)
        elif rule_type == "label_absent":
            self._rule_label_absent(rule, detections)
        else:
            self.logger.warning(f"Unknown rule type: {rule_type}")

    def _rule_positional_mismatch(self, rule: dict, detections: list[dict]) -> None:
        expected = rule["expected_label"]
        template = rule["flag_template"]
        start = rule.get("index_start", 0)
        for i, det in enumerate(detections):
            if det["label"] != expected:
                self._raised_flags.append(template.format(index=i + start))

    def _rule_label_present(self, rule: dict, detections: list[dict]) -> None:
        if any(d["label"] == rule["label"] for d in detections):
            self._raised_flags.append(rule["flag"])

    def _rule_label_absent(self, rule: dict, detections: list[dict]) -> None:
        if not any(d["label"] == rule["label"] for d in detections):
            self._raised_flags.append(rule["flag"])