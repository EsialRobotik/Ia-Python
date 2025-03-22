from ia.api.detection.ultrasound.srf import Srf
from ia.api.detection.ultrasound.srf04 import Srf04


class SrfFactory:
    @staticmethod
    def build_srf(srf_config: dict, window_size: int) -> Srf:
        """
        Build a Srf object from a config dict
        """
        if srf_config['type'] == 'srf04':
            return Srf04(
                trigger=srf_config['trigger'],
                echo=srf_config['echo'],
                x=srf_config['x'],
                y=srf_config['y'],
                angle=srf_config['angle'],
                threshold=srf_config['threshold'],
                window_size=window_size
            )
        raise ValueError(f"Unhandled SRF type : {srf_config['type']}")