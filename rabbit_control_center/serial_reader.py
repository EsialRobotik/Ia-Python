"""
Lecteur série pour le RabbitControlCenter.

Lit en continu (10 Hz côté émetteur) des trames du type :
    "0;1;1;1;0;0;0;1;0;1;0;1\n"
correspondant aux 12 interrupteurs (bp1..bp4 puis sw1..sw8).

Le worker pousse l'état via `ControlCenterState.set_switches`. Si la lecture
échoue (port indisponible, déconnexion), il retente toutes les secondes sans
bloquer le reste de l'application.
"""

import logging
import threading
import time

import serial

from rabbit_control_center.state import ControlCenterState, SWITCH_COUNT


logger = logging.getLogger(__name__)


class SerialSwitchReader:
    def __init__(self, state: ControlCenterState, port: str, baud_rate: int = 115200) -> None:
        self.state = state
        self.port = port
        self.baud_rate = baud_rate
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name='serial-switches')
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                with serial.Serial(self.port, self.baud_rate, timeout=1.0) as ser:
                    logger.info('Port série interrupteurs ouvert : %s', self.port)
                    self._read_loop(ser)
            except (serial.SerialException, OSError) as exc:
                logger.warning('Port série interrupteurs indisponible (%s) : %s — nouvelle tentative dans 1 s',
                               self.port, exc)
                time.sleep(1.0)

    def _read_loop(self, ser: serial.Serial) -> None:
        buffer = b''
        while not self._stop.is_set():
            try:
                data = ser.read(64)
            except (serial.SerialException, OSError) as exc:
                logger.warning('Erreur lecture série : %s', exc)
                return
            if not data:
                continue
            buffer += data
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                self._handle_line(line.strip())

    def _handle_line(self, raw: bytes) -> None:
        if not raw:
            return
        text = raw.decode(errors='replace').strip().rstrip(';')
        parts = [p.strip() for p in text.split(';') if p.strip() != '']
        if len(parts) != SWITCH_COUNT:
            return
        try:
            values = [bool(int(p)) for p in parts]
        except ValueError:
            return
        self.state.set_switches(values)
