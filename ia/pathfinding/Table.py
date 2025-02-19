import argparse
import json
from typing import List, Dict

from ia.pathfinding.shape.Circle import Circle
from ia.pathfinding.shape.Shape import Shape
from ia.pathfinding.shape.ShapeFactory import ShapeFactory
from ia.utils.Position import Position


class Table:
    """
    A class representing a table with various shapes and configurations.

    Attributes:
        x_size (int): The x-dimension size of the table.
        rectified_x_size (int): The rectified x-dimension size of the table.
        y_size (int): The y-dimension size of the table.
        rectified_y_size (int): The rectified y-dimension size of the table.
        color0 (str): The color at position 0.
        color3000 (str): The color at position 3000.
        margin (int): The margin size.
        forbidden_area (list[list[bool]]): The forbidden areas on the table.
        detection_ignore_quadrilaterium (list[list[Position]]): The quadrilaterium to ignore for detection.
        shape_list (list[Shape]): The list of shapes on the table.
        elements_list (dict[Shape, list[Position]]): The elements on the table with their positions.
    """

    def __init__(self, file_path: str = None) -> None:
        """
        Initializes the Table object. Optionally loads configuration from a file.

        Args:
            file_path (str, optional): The path to the configuration file.
        """
        self.x_size = 0
        self.rectified_x_size = 0
        self.y_size = 0
        self.rectified_y_size = 0
        self.color0 = ""
        self.color3000 = ""
        self.margin = 0
        self.forbidden_area = []
        self.detection_ignore_quadrilaterium = []
        self.shape_list = []
        self.elements_list = {}

        if file_path:
            self.load_from_save_file(file_path)

    def load_json_from_file(self, file_path: str) -> None:
        """
        Loads configuration from a JSON file.

        Args:
            file_path (str): The path to the JSON file.
        """
        with open(file_path, 'r') as reader:
            config_root_node = json.load(reader)
            self.load_config(config_root_node["table"])

    def load_json_from_file_with_skip(self, file_path: str, zone_to_skip: List[str]) -> None:
        """
        Loads configuration from a JSON file, skipping specified zones.

        Args:
            file_path (str): The path to the JSON file.
            zone_to_skip (list[str]): The list of zones to skip.
        """
        with open(file_path, 'r') as reader:
            config_root_node = json.load(reader)
            self.load_config(config_root_node["table"], zone_to_skip)
            self.draw_table()
            self.compute_forbidden_area()

    def load_json_from_string(self, json_str: str) -> None:
        """
        Loads configuration from a JSON string.

        Args:
            json_str (str): The JSON string.
        """
        config_root_node = json.loads(json_str)
        self.load_config(config_root_node)

    def load_from_save_file(self, filename: str) -> None:
        """
        Loads configuration from a save file.

        Args:
            filename (str): The path to the save file.
        """
        with open(filename, 'r') as file:
            lines = file.readlines()
            temp = lines[0].split(" ")
            self.x_size = int(temp[0])
            self.rectified_x_size = self.x_size // 10
            self.y_size = int(temp[1])
            self.rectified_y_size = self.y_size // 10

            self.forbidden_area = [[False] * self.rectified_y_size for _ in range(self.rectified_x_size)]
            for acc, line in enumerate(lines[1:]):
                for j, char in enumerate(line.strip()):
                    self.forbidden_area[acc][j] = (char == 'x')

    def load_config(self, root_element: dict, zone_to_skip: List[str] = None) -> None:
        """
        Loads configuration from a JSON object.

        Args:
            root_element (dict): The root JSON object.
            zone_to_skip (list[str], optional): The list of zones to skip.
        """
        self.shape_list = []
        self.x_size = root_element["sizeX"]
        self.rectified_x_size = self.x_size // 10
        self.y_size = root_element["sizeY"]
        self.rectified_y_size = self.y_size // 10
        self.color0 = root_element["color0"]
        self.color3000 = root_element["color3000"]
        self.margin = root_element["marge"]

        if zone_to_skip:
            for json_element in root_element["forbiddenZones"]:
                shape = ShapeFactory.get_shape(json_element)
                if shape.get_id() in zone_to_skip or "_margin" in shape.get_id():
                    continue
                self.shape_list.append(shape)

        self.elements_list = {}
        for json_element in root_element["dynamicZones"]:
            shape = ShapeFactory.get_shape(json_element)
            self.elements_list[shape] = self.get_points_from_shape(shape)

        self.detection_ignore_quadrilaterium = []
        for json_element in root_element["detectionIgnoreZone"]:
            points = [
                Position(json_element["x1"], json_element["y1"]),
                Position(json_element["x2"], json_element["y2"]),
                Position(json_element["x3"], json_element["y3"]),
                Position(json_element["x4"], json_element["y4"])
            ]
            self.add_points_to_detection_ignore_quadrilaterium(points)

    def add_points_to_detection_ignore_quadrilaterium(self, points: List[Position]) -> None:
        """
        Adds points to the detection ignore quadrilaterium.

        Args:
            points (list[Position]): The points to add.
        """
        self.detection_ignore_quadrilaterium.append(points)

    def get_x_size(self) -> int:
        """
        Gets the x-dimension size of the table.

        Returns:
            int: The x-dimension size.
        """
        return self.x_size

    def get_y_size(self) -> int:
        """
        Gets the y-dimension size of the table.

        Returns:
            int: The y-dimension size.
        """
        return self.y_size

    def get_rectified_x_size(self) -> int:
        """
        Gets the rectified x-dimension size of the table.

        Returns:
            int: The rectified x-dimension size.
        """
        return self.rectified_x_size

    def get_rectified_y_size(self) -> int:
        """
        Gets the rectified y-dimension size of the table.

        Returns:
            int: The rectified y-dimension size.
        """
        return self.rectified_y_size

    def get_color0_name(self) -> str:
        """
        Gets the color at position 0.

        Returns:
            str: The color at position 0.
        """
        return self.color0

    def get_color3000_name(self) -> str:
        """
        Gets the color at position 3000.

        Returns:
            str: The color at position 3000.
        """
        return self.color3000

    def get_shape_list(self) -> List[Shape]:
        """
        Gets the list of shapes on the table.

        Returns:
            list[Shape]: The list of shapes.
        """
        return self.shape_list

    def get_elements_list(self) -> Dict[Shape, List[Position]]:
        """
        Gets the elements on the table with their positions.

        Returns:
            dict[Shape, list[Position]]: The elements and their positions.
        """
        return self.elements_list

    def find_element_by_id(self, item_id: str) -> List[Position]:
        """
        Finds an element by its ID.

        Args:
            item_id (str): The ID of the element.

        Returns:
            list[Position]: The positions of the element.
        """
        for shape, points in self.elements_list.items():
            if shape.get_id() == item_id:
                return points
        return []

    def draw_table(self) -> None:
        """
        Draws the table by marking forbidden areas.
        """
        self.forbidden_area = [[False] * self.rectified_y_size for _ in range(self.rectified_x_size)]
        for shape in self.shape_list:
            temp = shape.draw_shape_edges(self.rectified_x_size, self.rectified_y_size)
            for i in range(self.rectified_x_size):
                for j in range(self.rectified_y_size):
                    if temp[i + self.rectified_x_size][j + self.rectified_y_size]:
                        self.forbidden_area[i][j] = True

    def set_value(self, board: List[List[bool]], x: int, y: int, val: bool) -> None:
        """
        Sets a value on the board if within bounds.

        Args:
            board (list[list[bool]]): The board.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            val (bool): The value to set.
        """
        if 0 <= x < len(board) and 0 <= y < len(board[0]):
            board[x][y] = val

    def compute_forbidden_area(self) -> None:
        """
        Computes the forbidden areas on the table.
        """
        rectified_margin = (self.margin + 9) // 10
        board_length = len(self.forbidden_area)
        board_width = len(self.forbidden_area[0])

        buffer = [[False] * (board_width + 2 * (rectified_margin + 1)) for _ in range(board_length + 2 * (rectified_margin + 1))]
        circle = Circle(rectified_margin * 10, rectified_margin * 10, rectified_margin * 10)
        buffer_size = (rectified_margin + 1) * 2
        shape_buffer = circle.draw_shape_edges(buffer_size, buffer_size)

        for i in range(board_length):
            for j in range(board_width):
                if self.forbidden_area[i][j]:
                    for i1 in range(buffer_size, buffer_size * 2):
                        for j1 in range(buffer_size, buffer_size * 2):
                            if shape_buffer[i1][j1]:
                                self.set_value(buffer, i + 1 + i1 - buffer_size, j + 1 + j1 - buffer_size, True)
                                self.set_value(buffer, i + 2 + i1 - buffer_size, j + 1 + j1 - buffer_size, True)
                                self.set_value(buffer, i + 1 + i1 - buffer_size, j + 2 + j1 - buffer_size, True)
                                self.set_value(buffer, i + 2 + i1 - buffer_size, j + 2 + j1 - buffer_size, True)

        for i1 in range(rectified_margin + 1, board_length + rectified_margin + 1):
            for j1 in range(rectified_margin + 1, board_width + rectified_margin + 1):
                if buffer[i1][j1]:
                    self.forbidden_area[i1 - rectified_margin - 1][j1 - rectified_margin - 1] = True

        for i in range(rectified_margin):
            for j in range(self.rectified_y_size):
                self.forbidden_area[i][j] = True

        for i in range(self.rectified_x_size - rectified_margin, self.rectified_x_size):
            for j in range(self.rectified_y_size):
                self.forbidden_area[i][j] = True

        for i in range(self.rectified_x_size):
            for j in range(rectified_margin):
                self.forbidden_area[i][j] = True
            for j in range(self.rectified_y_size - rectified_margin, self.rectified_y_size):
                self.forbidden_area[i][j] = True

    def compute_forbidden_area_for_element(self, element: List[List[bool]]) -> List[List[bool]]:
        """
        Computes the forbidden areas for a specific element.

        Args:
            element (list[list[bool]]): The element.

        Returns:
            list[list[bool]]: The updated element with forbidden areas.
        """
        rectified_margin = (self.margin + 9) // 10
        board_length = len(element)
        board_width = len(element[0])

        buffer = [[False] * (board_width + 2 * (rectified_margin + 1)) for _ in range(board_length + 2 * (rectified_margin + 1))]
        circle = Circle(rectified_margin * 10, rectified_margin * 10, rectified_margin * 10)
        buffer_size = (rectified_margin + 1) * 2
        shape_buffer = circle.draw_shape_edges(buffer_size, buffer_size, False)

        for i in range(board_length):
            for j in range(board_width):
                if element[i][j]:
                    for i1 in range(buffer_size, buffer_size * 2):
                        for j1 in range(buffer_size, buffer_size * 2):
                            if shape_buffer[i1][j1]:
                                self.set_value(buffer, i + 1 + i1 - buffer_size, j + 1 + j1 - buffer_size, True)
                                self.set_value(buffer, i + 2 + i1 - buffer_size, j + 1 + j1 - buffer_size, True)
                                self.set_value(buffer, i + 1 + i1 - buffer_size, j + 2 + j1 - buffer_size, True)
                                self.set_value(buffer, i + 2 + i1 - buffer_size, j + 2 + j1 - buffer_size, True)

        for i1 in range(rectified_margin + 1, board_length + rectified_margin + 1):
            for j1 in range(rectified_margin + 1, board_width + rectified_margin + 1):
                if buffer[i1][j1]:
                    element[i1 - rectified_margin - 1][j1 - rectified_margin - 1] = True

        for i in range(rectified_margin):
            for j in range(self.rectified_y_size):
                element[i][j] = True

        for i in range(self.rectified_x_size - rectified_margin, self.rectified_x_size):
            for j in range(self.rectified_y_size):
                element[i][j] = True

        for i in range(self.rectified_x_size):
            for j in range(rectified_margin):
                element[i][j] = True
            for j in range(self.rectified_y_size - rectified_margin, self.rectified_y_size):
                element[i][j] = True

        return element

    def get_zone_points_by_id(self, margin: int, forbidden_zone_id: str) -> List[Position]:
        """
        Gets the points of a zone by its ID.

        Args:
            margin (int): The margin size.
            forbidden_zone_id (str): The ID of the forbidden zone.

        Returns:
            list[Position]: The points of the zone.

        Raises:
            Exception: If the shape is not found.
        """
        clean_shape = next((shape for shape in self.shape_list if shape.get_id() == forbidden_zone_id), None)
        if not clean_shape:
            raise Exception(f"Unknown shape {forbidden_zone_id}")

        points = []
        shape_buffer = clean_shape.draw_shape_edges(self.rectified_x_size, self.rectified_y_size)
        rectified_margin = (margin + 9) // 10
        buffer_size = (rectified_margin + 1) * 2

        for i in range(self.rectified_x_size, len(shape_buffer) - self.rectified_x_size):
            for j in range(self.rectified_y_size, len(shape_buffer[0]) - self.rectified_y_size):
                if shape_buffer[i][j]:
                    points.append(Position(i - self.rectified_x_size, j - self.rectified_y_size))
                    for i1 in range(buffer_size, buffer_size * 2):
                        for j1 in range(buffer_size, buffer_size * 2):
                            if 0 < i + 1 + i1 - buffer_size <= self.rectified_x_size:
                                if 0 < j + 1 + j1 - buffer_size <= self.rectified_y_size:
                                    points.append(Position(i + 1 + i1 - buffer_size - self.rectified_x_size, j + 1 + j1 - buffer_size - self.rectified_y_size))
                                if 0 < j + 2 + j1 - buffer_size <= self.rectified_y_size:
                                    points.append(Position(i + 1 + i1 - buffer_size - self.rectified_x_size, j + 2 + j1 - buffer_size - self.rectified_y_size))
                            if 0 < i + 2 + i1 - buffer_size <= self.rectified_x_size:
                                if 0 < j + 1 + j1 - buffer_size <= self.rectified_y_size:
                                    points.append(Position(i + 2 + i1 - buffer_size - self.rectified_x_size, j + 1 + j1 - buffer_size - self.rectified_y_size))
                                if 0 < j + 2 + j1 - buffer_size <= self.rectified_y_size:
                                    points.append(Position(i + 2 + i1 - buffer_size - self.rectified_x_size, j + 2 + j1 - buffer_size - self.rectified_y_size))

        return points

    def print_table(self) -> None:
        """
        Prints the table with forbidden areas.
        """
        for row in self.forbidden_area:
            print("".join("x" if cell else "o" for cell in row))

    def print_buffer(self, buffer: List[List[bool]]) -> None:
        """
        Prints a buffer.

        Args:
            buffer (list[list[bool]]): The buffer to print.
        """
        for row in buffer:
            print("".join("x" if cell else "o" for cell in row))

    def __str__(self) -> str:
        """
        Returns a string representation of the table.

        Returns:
            str: The string representation.
        """
        return "\n".join("".join("x" if cell else "o" for cell in row) for row in self.forbidden_area)

    def save_to_file(self, filename: str) -> None:
        """
        Saves the table configuration to a file.

        Args:
            filename (str): The path to the file.
        """
        with open(filename, 'w') as file:
            file.write(f"{self.get_x_size()} {self.get_y_size()}\n")
            file.write(str(self))

    def is_area_forbidden(self, x: int, y: int) -> bool:
        """
        Checks if a position is in a forbidden zone or outside the table.

        Args:
            x (int): The x-coordinate.
            y (int): The y-coordinate.

        Returns:
            bool: True if outside the table or in a forbidden zone.
        """
        if x < 0 or y < 0 or x >= self.rectified_x_size or y >= self.rectified_y_size:
            return True
        return self.forbidden_area[x][y]

    def is_point_in_detection_ignore_zone(self, point: Position) -> bool:
        """
        Checks if a point is in a detection ignore zone.
        TODO: Works only with quadrilaterals aligned on the table with points in order.
        TODO: Improve to handle better cases.

        Args:
            point (Position): The point to check.

        Returns:
            bool: True if the point is in a detection ignore zone.
        """
        for quadrilaterium in self.detection_ignore_quadrilaterium:
            if (quadrilaterium[0].x <= point.x <= quadrilaterium[2].x
                    and quadrilaterium[0].y <= point.y <= quadrilaterium[2].y):
                return True
        return False

    def get_points_from_shape(self, shape: Shape) -> List[Position]:
        """
        Gets the points from a shape.

        Args:
            shape (Shape): The shape to get points from.

        Returns:
            list[Position]: The list of points from the shape.
        """
        points = []
        temp = shape.draw_shape_edges(self.rectified_x_size, self.rectified_y_size, False)
        temp = self.compute_forbidden_area_for_element(temp)
        for i in range(self.rectified_x_size, self.rectified_x_size * 2 + 1):
            for j in range(self.rectified_y_size, self.rectified_y_size * 2 + 1):
                if temp[i][j]:
                    points.append(Position(i - self.rectified_x_size, j - self.rectified_y_size))
        return points

if __name__ == "__main__":
    # manage arguments
    parser = argparse.ArgumentParser(description="Process a year.")
    parser.add_argument("year", type=int, help="Year in integer format")
    args = parser.parse_args()
    file_path = f'config/{args.year}/config.json'
    table = Table()
    table.load_json_from_file_with_skip(f"config/{args.year}/config.json", [])
    table.draw_table()
    table.compute_forbidden_area()
    table.save_to_file(f"config/{args.year}/table0.tbl")

    table = Table()
    table.load_json_from_file_with_skip(f"config/{args.year}/config.json", [])
    table.draw_table()
    table.compute_forbidden_area()
    table.save_to_file(f"config/{args.year}/table3000.tbl")

    print("Generation of the table successful.")