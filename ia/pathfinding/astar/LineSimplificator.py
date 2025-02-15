from typing import List, Collection, Optional

from ia.utils.Position import Position, Direction


class LineSimplificator:
    """
    A class to simplify paths calculated by the A* algorithm.
    Works correctly if the paths are straight lines of 0°, 45°, 90°, etc...
    and if the points are adjacent (i.e. the coordinate difference between two
    successive points is at most 1).
    """

    @staticmethod
    def get_simple_lines(path: Collection[Position]) -> Optional[List[Position]]:
        """
        Simplifies a path by keeping only the points corresponding to
        straight line segments.

        Args:
            path (Collection[Position]): The complicated path

        Returns:
            Optional[List[Position]]: A simpler path
        """
        # If there is no path, return None
        if path is None:
            return None

        # If the path is empty, return an empty list
        if len(path) == 0:
            return []

        # The list of points for the simple path
        simple_path = []

        # We don't know the direction of the segment
        direction = Direction.NULL

        # The previous point, because we will need it
        previous = None

        # We go through all the points
        for current in path:
            if previous is None:
                # Initial case: add the first point to the simple path
                simple_path.append(current)
            elif direction == Direction.NULL:
                # We don't know the direction of the line yet, it's the beginning,
                # we will calculate it
                direction = previous.get_direction_to_go_to(current)
            else:
                # Get the new direction
                new_direction = previous.get_direction_to_go_to(current)

                # The direction changes!
                if new_direction != direction:
                    # The previous point is the end of a straight line segment, add it to the simple path
                    simple_path.append(previous)
                    direction = new_direction  # Change direction
            # Save the point
            previous = current

        # We still need to add the last point
        if previous is not None and previous not in simple_path:
            simple_path.append(previous)

        return simple_path