import importlib
import logging
import sys

if __name__ == "__main__":
    logging.getLogger('').setLevel(logging.getLevelNamesMapping()['DEBUG'])
    stdout_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stdout_handler.setFormatter(formatter)
    logging.getLogger().addHandler(stdout_handler)

    strategies = [
        ('strategy.main.2025.freddy_princess', 'FreddyPrincess'),
        ('strategy.main.2025.pami_star',       'PamiStar'),
        ('strategy.main.2025.pami_2',          'Pami2'),
        ('strategy.main.2025.pami_3',          'Pami3'),
        ('strategy.main.2025.pami_4',          'Pami4'),
    ]

    for module_path, class_name in strategies:
        module = importlib.import_module(module_path)
        getattr(module, class_name)().generate()