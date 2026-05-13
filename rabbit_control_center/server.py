"""
Serveurs TCP du RabbitControlCenter :
- LogServer : reçoit les LogRecord pickled (port 9020), écrit dans logs/
- CommServer : relais inter-robots (port 4269), conserve la fonctionnalité existante
  et étend le protocole d'identification (`robot#<id>`) et de couleur (`color#<color>`).

Les deux serveurs s'exécutent dans des threads daemon et notifient l'UI via
le hub `ControlCenterState`.
"""

import logging
import logging.handlers
import os
import pickle
import socket
import socketserver
import struct
import threading
import time
from typing import Optional

from rabbit_control_center.state import ControlCenterState

INACTIVITY_ROTATION_SECONDS = 600
# Logs reçus des robots (port 9020) : champ `who` injecté par chaque robot.
ROBOT_LOG_FORMAT = '%(asctime)s - %(who)s - %(levelname)s - %(message)s'
# Logs internes du RCC : pas de champ `who`, on garde le name du logger.
RCC_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

logger = logging.getLogger(__name__)


def build_rcc_file_handler(log_dir: str) -> logging.handlers.RotatingFileHandler:
    """Crée le RotatingFileHandler pour les logs internes du RCC.

    Fichier distinct des logs robots (`server-log.log`) — l'utilisateur veut
    pouvoir trier rapidement "ce qui s'est passé côté serveur" vs "ce qui s'est
    passé côté robot" après un match.
    """
    os.makedirs(log_dir, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'rcc.log'),
        backupCount=50,
    )
    handler.doRollover()
    handler.setFormatter(logging.Formatter(RCC_LOG_FORMAT))
    return handler


class _ServerContext:
    """Contexte partagé entre handlers (file handler robots, listeners, état).

    Gère uniquement le flux de logs **robots** : le file handler RCC vit
    indépendamment, attaché au root logger côté `main.py`.
    """

    def __init__(self, state: ControlCenterState, log_dir: str,
                 rcc_file_handler: Optional[logging.Handler] = None) -> None:
        self.state = state
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self._formatter = logging.Formatter(ROBOT_LOG_FORMAT)
        self.robot_file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, 'server-log.log'),
            backupCount=50,
        )
        self.robot_file_handler.doRollover()
        self.robot_file_handler.setFormatter(self._formatter)

        # Le handler RCC est créé par main.py et passé ici uniquement pour
        # que `rotate_logs()` puisse aussi le faire tourner — le RCC n'écrit
        # PAS dans ce fichier via _ServerContext.
        self._rcc_file_handler = rcc_file_handler

        self._activity_lock = threading.Lock()
        self._last_log_time: Optional[float] = None
        self._rotation_lock = threading.Lock()

        # Socket abonnés au flux de logs (anciens "logListener")
        self._log_listeners_lock = threading.Lock()
        self._log_listeners: list[socket.socket] = []

        # Renseigné après démarrage des serveurs (CommServer instancié).
        # L'UI y accède directement pour broadcaster (cf. main.py).
        self.comm_server: Optional['CommServer'] = None

    def rotate_logs(self) -> None:
        """Force un rollover des deux fichiers de logs (robots + RCC).

        Appelé à chaque retour sur le tableau de bord pour qu'un match
        terminé occupe son propre couple de fichiers, plus simple à archiver.
        """
        with self._rotation_lock:
            self.robot_file_handler.doRollover()
            if self._rcc_file_handler is not None:
                self._rcc_file_handler.doRollover()
            with self._activity_lock:
                self._last_log_time = None
        logger.info("Rotation des logs effectuée (robots + RCC)")

    # --- Logs : écriture fichier + relai aux listeners ------------------------

    def write_log_record(self, record: logging.LogRecord) -> None:
        line = self._formatter.format(record)
        self.robot_file_handler.handle(record)
        with self._activity_lock:
            self._last_log_time = time.monotonic()

        encoded = (line + '\n').encode()
        with self._log_listeners_lock:
            dead: list[socket.socket] = []
            for sock in self._log_listeners:
                try:
                    sock.sendall(encoded)
                except OSError:
                    dead.append(sock)
            for sock in dead:
                self._log_listeners.remove(sock)
                try:
                    sock.close()
                except OSError:
                    pass

        # Notifier l'UI
        who = getattr(record, 'who', '')
        message = record.getMessage()
        self.state.log_record.emit(line)
        self.state.log_record_parsed.emit(
            time.strftime('%H:%M:%S'),
            str(who),
            record.levelname,
            message,
        )
        stripped = message.strip()
        if stripped == 'Match lancé':
            self.state.declare_match_started()
            if who:
                self.state.set_robot_ready(str(who), False)
        elif stripped == 'Attente lancement match' and who:
            self.state.set_robot_ready(str(who), True)

    def add_log_listener(self, sock: socket.socket) -> None:
        with self._log_listeners_lock:
            self._log_listeners.append(sock)
        try:
            sock.sendall(b'logListener connected')
        except OSError:
            pass

    def remove_log_listener(self, sock: socket.socket) -> None:
        with self._log_listeners_lock:
            if sock in self._log_listeners:
                self._log_listeners.remove(sock)

    # --- Surveillance d'inactivité --------------------------------------------

    def inactivity_watcher(self) -> None:
        check_interval = max(1, INACTIVITY_ROTATION_SECONDS // 20)
        while True:
            time.sleep(check_interval)
            should_rotate = False
            with self._activity_lock:
                if self._last_log_time is None:
                    continue
                if time.monotonic() - self._last_log_time >= INACTIVITY_ROTATION_SECONDS:
                    should_rotate = True
                    self._last_log_time = None
            if should_rotate:
                with self._rotation_lock:
                    self.robot_file_handler.doRollover()
                logger.info("Rotation du log robots après %ds d'inactivité",
                            INACTIVITY_ROTATION_SECONDS)


# --- Serveur de logs (pickled LogRecord) -------------------------------------

class _LogStreamHandler(socketserver.StreamRequestHandler):
    server: 'LogServer'

    def handle(self) -> None:
        ctx: _ServerContext = self.server.context
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack('>L', chunk)[0]
            chunk = b''
            while len(chunk) < slen:
                received = self.connection.recv(slen - len(chunk))
                if not received:
                    return
                chunk += received
            obj = pickle.loads(chunk)
            record = logging.makeLogRecord(obj)
            ctx.write_log_record(record)


class LogServer(socketserver.ThreadingTCPServer):
    """Reçoit les LogRecord pickled. Compatible avec `logging.handlers.SocketHandler`."""

    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, host: str, port: int, context: _ServerContext) -> None:
        super().__init__((host, port), _LogStreamHandler)
        self.context = context
        self.timeout = 1


def start_log_server(host: str, port: int, context: _ServerContext) -> LogServer:
    server = LogServer(host, port, context)
    thread = threading.Thread(target=server.serve_forever, daemon=True, name='log-server')
    thread.start()
    return server


# --- Serveur de communication inter-robots -----------------------------------

class CommServer:
    """
    Serveur TCP qui :
    - accepte des connexions de robots et de log listeners
    - relaie les messages reçus d'un robot à tous les autres robots
    - intercepte les messages d'identité (`robot#<id>`) et de couleur (`color#<color>`)
      pour mettre à jour l'état affiché par l'UI

    Compatible avec l'ancien protocole (`robot` seul, `logListener`).
    """

    def __init__(self, host: str, port: int, context: _ServerContext) -> None:
        self.host = host
        self.port = port
        self.context = context
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((host, port))
        self._sock.listen(16)
        self._robots_lock = threading.Lock()
        # robot_conn -> robot_id (peut être None si l'ancien protocole "robot" est utilisé)
        self._robots: dict[socket.socket, Optional[str]] = {}

    def serve_forever(self) -> None:
        while True:
            try:
                conn, address = self._sock.accept()
            except OSError:
                break
            threading.Thread(
                target=self._handle_initial,
                args=(conn, address),
                daemon=True,
                name=f'comm-{address}',
            ).start()

    # --- Premier message : identification ------------------------------------

    def _handle_initial(self, conn: socket.socket, address) -> None:
        try:
            data = conn.recv(1024).decode(errors='replace').strip()
        except OSError:
            conn.close()
            return
        if not data:
            conn.close()
            return

        if data == 'logListener':
            self.context.add_log_listener(conn)
            # Garder la socket ouverte ; on la libère quand le client se déconnecte.
            threading.Thread(
                target=self._watch_listener,
                args=(conn,),
                daemon=True,
                name=f'log-listener-{address}',
            ).start()
            return

        # Sinon : robot. Format possible : "robot" (legacy) ou "robot#<id>"
        robot_id: Optional[str] = None
        if data.startswith('robot'):
            if '#' in data:
                robot_id = data.split('#', 1)[1].strip() or None
        else:
            # Premier message inattendu : on traite comme un robot anonyme et on
            # injecte ce message dans le flux normal pour ne rien perdre.
            self._enqueue_robot(conn, robot_id=None)
            self._dispatch_message(conn, data)
            self._read_loop(conn)
            return

        self._enqueue_robot(conn, robot_id=robot_id)
        self._read_loop(conn)

    def _enqueue_robot(self, conn: socket.socket, robot_id: Optional[str]) -> None:
        with self._robots_lock:
            self._robots[conn] = robot_id
        logger.info("Robot connecté : id=%s (peer=%s)", robot_id or '?',
                    conn.getpeername() if conn else '?')
        if robot_id:
            self.context.state.set_robot_connected(robot_id, True)

    def _watch_listener(self, conn: socket.socket) -> None:
        # Le log listener n'envoie rien ; on attend la fermeture de la socket.
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
        except OSError:
            pass
        finally:
            self.context.remove_log_listener(conn)
            try:
                conn.close()
            except OSError:
                pass

    # --- Boucle de lecture pour un robot connecté ----------------------------

    def _read_loop(self, conn: socket.socket) -> None:
        buffer = ''
        try:
            while True:
                try:
                    data = conn.recv(1024).decode(errors='replace')
                except OSError:
                    break
                if not data:
                    break
                buffer += data
                # Les messages sont auto-délimités côté robot (un send par message).
                # On découpe sur retour à la ligne au cas où plusieurs sont concaténés.
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        self._dispatch_message(conn, line)
                if buffer:
                    self._dispatch_message(conn, buffer)
                    buffer = ''
        finally:
            self._on_disconnect(conn)

    def _on_disconnect(self, conn: socket.socket) -> None:
        with self._robots_lock:
            robot_id = self._robots.pop(conn, None)
        logger.info("Robot déconnecté : id=%s", robot_id or '?')
        if robot_id:
            self.context.state.set_robot_connected(robot_id, False)
        try:
            conn.close()
        except OSError:
            pass

    def _dispatch_message(self, conn: socket.socket, message: str) -> None:
        # Messages internes : non re-broadcastés
        if message.startswith('color#'):
            color = message.split('#', 1)[1].strip()
            with self._robots_lock:
                robot_id = self._robots.get(conn)
            if robot_id and color:
                logger.info("Couleur reçue pour %s : %s", robot_id, color)
                self.context.state.set_robot_color(robot_id, color)
            return
        if message.startswith('hello#'):
            robot_id = message.split('#', 1)[1].strip()
            if robot_id:
                with self._robots_lock:
                    self._robots[conn] = robot_id
                logger.info("Identification tardive du robot : %s", robot_id)
                self.context.state.set_robot_connected(robot_id, True)
            return

        # Tout le reste : broadcast aux autres robots (comportement historique)
        self._broadcast(message, exclude=conn)

    def _broadcast(self, message: str, exclude: Optional[socket.socket] = None) -> None:
        """Envoie un message à tous les robots connectés (sauf `exclude`)."""
        encoded = message.encode()
        with self._robots_lock:
            peers = [c for c in self._robots if c is not exclude]
        dead = []
        for peer in peers:
            try:
                peer.sendall(encoded)
            except OSError:
                dead.append(peer)
        for peer in dead:
            self._on_disconnect(peer)

    def broadcast_to_robots(self, message: str) -> None:
        """Envoie un message à tous les robots connectés (initiative serveur).

        Distinct du broadcast déclenché par la réception d'un message robot
        (cf. `_dispatch_message` / `_broadcast`) : ici on n'exclut personne car
        l'émetteur est le RCC, pas un robot.
        """
        if not message:
            return
        with self._robots_lock:
            count = len(self._robots)
        logger.info("Broadcast aux %d robot(s) : %s", count, message)
        self._broadcast(message, exclude=None)


def start_comm_server(host: str, port: int, context: _ServerContext) -> CommServer:
    server = CommServer(host, port, context)
    thread = threading.Thread(target=server.serve_forever, daemon=True, name='comm-server')
    thread.start()
    return server


# --- Façade ------------------------------------------------------------------

def start_servers(state: ControlCenterState, log_dir: str,
                  com_port: int, log_port: int,
                  rcc_file_handler: Optional[logging.Handler] = None) -> _ServerContext:
    """Démarre les deux serveurs et le watcher d'inactivité, retourne le contexte.

    `rcc_file_handler` (optionnel) : handler RCC créé en amont par main.py et
    attaché au root logger. Passé ici uniquement pour que `rotate_logs()` puisse
    aussi le faire tourner — son cycle de vie reste piloté par main.py.
    """
    context = _ServerContext(state=state, log_dir=log_dir,
                             rcc_file_handler=rcc_file_handler)
    threading.Thread(target=context.inactivity_watcher, daemon=True,
                     name='inactivity-watcher').start()
    start_log_server('', log_port, context)
    context.comm_server = start_comm_server('', com_port, context)
    return context
