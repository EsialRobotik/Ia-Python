from typing import List, Optional

from strategy.core.objective import Objective


class Strat:
    def __init__(self, couleur0: Optional[List[Objective]] = None, couleur3000: Optional[List[Objective]] = None):
        self.couleur0 = couleur0 if couleur0 is not None else []
        self.couleur3000 = couleur3000 if couleur3000 is not None else []

    def to_dict(self):
        return {
            "color0": [obj.to_dict() for obj in self.couleur0],
            "color3000": [obj.to_dict() for obj in self.couleur3000]
        }

    def __str__(self) -> str:
        couleur0_str = "\t\t".join([str(obj) for obj in self.couleur0])
        couleur3000_str = "\t\t".join([str(obj) for obj in self.couleur3000])
        return (
            "Strat{"
            f"\n\tcolor0=[\t\t{couleur0_str}\n\t],"
            f"\n\tcolor3000=[\t\t{couleur3000_str}\n\t]"
            "\n}"
        )