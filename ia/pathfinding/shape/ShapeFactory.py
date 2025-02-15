from ia.pathfinding.shape.Circle import Circle
from ia.pathfinding.shape.Polygon import Polygon
from ia.pathfinding.shape.Shape import Shape

class ShapeFactory:
    @staticmethod
    def get_shape(json_object: dict) -> Shape:
        """
        Returns a Shape object based on the provided JSON object.

        Args:
            json_object (dict): A dictionary containing the shape's properties.

        Returns:
            Shape: An instance of a Shape subclass (Circle or Polygon).

        Raises:
            RuntimeError: If the shape type is not recognized.
        """
        shape_name = json_object["forme"]
        if shape_name == "cercle":
            return Circle(json_object=json_object)
        elif shape_name == "polygone":
            return Polygon(json_object=json_object)
        else:
            raise RuntimeError(f"Shape {shape_name} cannot be loaded")