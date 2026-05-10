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
LOG_FORMAT = '%(asctime)s - %(who)s - %(levelname)s - %(message)s'


class _ServerContext:
    """Contexte partagé entre handlers (file handler, listeners, état)."""

    def __init__(self, state: ControlCenterState, log_dir: str) -> None:
        self.state = state
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self._formatter = logging.Formatter(LOG_FORMAT)
        self._file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, 'server-log.log'),
            backupCount=50,
        )
        self._file_handler.doRollover()
        self._file_handler.setFormatter(self._formatter)

        self._activity_lock = threading.Lock()
        self._last_log_time: Optional[float] = None

        # Socket abonnés au flux de logs (anciens "logListener")
        self._log_listeners_lock = threading.Lock()
        self._log_listeners: list[socket.socket] = []

    # --- Logs : écriture fichier + relai aux listeners ------------------------

    def write_log_record(self, record: logging.LogRecord) -> None:
        line = self._formatter.format(record)
        self._file_handler.handle(record)
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
        if message.strip() == 'Match lancé':
            self.state.declare_match_started()

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
            with self._activity_lock:
                if self._last_log_time is None:
                    continue
                if time.monotonic() - self._last_log_time >= INACTIVITY_ROTATION_SECONDS:
                    self._file_handler.doRollover()
                    self._last_log_time = None


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
                self.context.state.set_robot_color(robot_id, color)
            return
        if message.startswith('hello#'):
            robot_id = message.split('#', 1)[1].strip()
            if robot_id:
                with self._robots_lock:
                    self._robots[conn] = robot_id
                self.context.state.set_robot_connected(robot_id, True)
            return

        # Tout le reste : broadcast aux autres robots (comportement historique)
        encoded = message.encode()
        with self._robots_lock:
            peers = [c for c in self._robots if c is not conn]
        dead = []
        for peer in peers:
            try:
                peer.sendall(encoded)
            except OSError:
                dead.append(peer)
        for peer in dead:
            self._on_disconnect(peer)


def start_comm_server(host: str, port: int, context: _ServerContext) -> CommServer:
    server = CommServer(host, port, context)
    thread = threading.Thread(target=server.serve_forever, daemon=True, name='comm-server')
    thread.start()
    return server


# --- Façade ------------------------------------------------------------------

def start_servers(state: ControlCenterState, log_dir: str,
                  com_port: int, log_port: int) -> _ServerContext:
    """Démarre les deux serveurs et le watcher d'inactivité, retourne le contexte."""
    context = _ServerContext(state=state, log_dir=log_dir)
    threading.Thread(target=context.inactivity_watcher, daemon=True,
                     name='inactivity-watcher').start()
    start_log_server('', log_port, context)
    start_comm_server('', com_port, context)
    return context
