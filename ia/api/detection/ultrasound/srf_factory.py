from ia.api.detection.ultrasound.srf import Srf
from ia.api.detection.ultrasound.srf04 import Srf04
from ia.api.detection.ultrasound.srf08 import Srf08


class SrfFactory:
    @staticmethod
    def build_srf(srf_config: dict, window_size: int) -> Srf:
        """
        Build a Srf object from a config dict
        """
        if srf_config['type'] == 'srf04':
            return Srf04(
                desc=srf_config['desc'],
                trigger=srf_config['trigger'],
                echo=srf_config['echo'],
                x=srf_config['x'],
                y=srf_config['y'],
                angle=srf_config['angle'],
                threshold=srf_config['threshold'],
                window_size=window_size
            )
        elif srf_config['type'] == 'srf08':
            return Srf08(
                desc=srf_config['desc'],
                address=srf_config['address'],
                x=srf_config['x'],
                y=srf_config['y'],
                angle=srf_config['angle'],
                threshold=srf_config['threshold'],
                window_size=window_size
            )
        raise ValueError(f"Unhandled SRF type : {srf_config['type']}")