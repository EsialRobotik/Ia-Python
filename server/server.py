import logging
import logging.handlers
import os
import pickle
import socket
import socketserver
import struct
import sys
import threading
import time

# Délai d'inactivité (en secondes) avant de déclencher une rotation des logs
INACTIVITY_ROTATION_SECONDS = 600

log_listener = None
_log_formatter = logging.Formatter('%(asctime)s - %(who)s - %(levelname)s - %(message)s')
_file_handler = None
_last_log_time = None
_log_activity_lock = threading.Lock()


def setup_logging():
    global _file_handler
    os.makedirs('logs', exist_ok=True)
    _file_handler = logging.handlers.RotatingFileHandler(filename='logs/server-log.log', backupCount=50)
    _file_handler.doRollover()
    _file_handler.setFormatter(_log_formatter)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(_log_formatter)
    root = logging.getLogger()
    root.addHandler(_file_handler)
    root.addHandler(stdout_handler)


def inactivity_rotation_watcher():
    """
    Surveille l'activité de log et déclenche un rollover du fichier
    courant après INACTIVITY_ROTATION_SECONDS sans message reçu.
    """
    global _last_log_time
    check_interval = max(1, INACTIVITY_ROTATION_SECONDS // 20)
    while True:
        time.sleep(check_interval)
        with _log_activity_lock:
            if _last_log_time is None:
                continue
            if time.monotonic() - _last_log_time >= INACTIVITY_ROTATION_SECONDS:
                _file_handler.doRollover()
                _last_log_time = None

class Server:
    """
    A class to represent the server that handles communication with robots and logging.
    """

    def __init__(self) -> None:
        """
        Initializes the Server instance.
        """
        self.robots = []
        
        self.init_communication_server()
        self.tcpserver = LogRecordSocketReceiver()
        print('About to start TCP server...')
        self.tcpserver.serve_until_stopped()

    def init_communication_server(self) -> None:
        """
        Initializes the communication server socket and starts a thread to accept connections.
        """
        self.communication_server_socket = socket.socket()
        self.communication_server_socket.bind(('', 4269)) # empty host allow any ip to connect
        self.communication_server_socket.listen(10)
        comm_connection_thread = threading.Thread(target=self.accept_communication_connection)
        comm_connection_thread.daemon = True
        comm_connection_thread.start()

    def accept_communication_connection(self) -> None:
        """
        Accepts incoming connections and handles them based on the type of connection.
        """
        global log_listener
        while True:
            conn, address = self.communication_server_socket.accept()
            print("Connection from: " + str(address))
            data = conn.recv(1024).decode()
            if not data:
                conn.close()
                self.robots.remove(conn)
                print("Accept connection closed")
                break
            print("from connected user: " + str(data))
            if data == "robot":
                self.robots.append(conn)
                comm_robots_thread = threading.Thread(target=self.communication_between_robots, args=(conn,))
                comm_robots_thread.daemon = True
                comm_robots_thread.start()
            elif data == "logListener":
                log_listener = conn
                print("logListener connected")
                log_listener.send("logListener connected".encode())

    def communication_between_robots(self, conn: socket):
        """
        Handles communication between connected robots.

        This method continuously listens for messages from a connected robot
        and forwards the received messages to all other connected robots.

        Args:
            conn (socket): The socket connection to the robot.
        """
        while True:
            data = conn.recv(1024).decode()
            print("from connected robot: " + str(data))
            if not data:
                conn.close()
                self.robots.remove(conn)
                print("Robot connection closed")
                break
            for robot in self.robots:
                robot.send(data.encode())

class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """
    Handler for a streaming logging request.

    This basically logs the record using whatever logging policy is
    configured locally.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """

        global log_listener, _last_log_time
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack('>L', chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unPickle(chunk)

            record = logging.makeLogRecord(obj)
            logging.getLogger('').handle(record)
            with _log_activity_lock:
                _last_log_time = time.monotonic()
            if log_listener is not None:
                log_listener.send((_log_formatter.format(record) + '\n').encode())

    def unPickle(self, data):
        """
        Unpickles the given data.

        Args:
            data (bytes): The pickled data to unpickle.

        Returns:
            object: The unpickled Python object.
        """
        return pickle.loads(data)

class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
    Simple TCP socket-based logging receiver suitable for testing.
    """

    allow_reuse_address = True

    def __init__(self, host='',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 handler=LogRecordStreamHandler) -> None:
        """
        Simple TCP socket-based logging receiver suitable for testing.
        """

        socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1
        self.logname = None

    def serve_until_stopped(self):
        """
        Serve requests until the server is stopped.

        This method uses the `select` module to wait for incoming connections
        and handle them. It continues to serve requests until the `abort`
        attribute is set to a non-zero value.
        """

        import select
        abort = 0
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort

if __name__ == '__main__':
    setup_logging()
    watcher_thread = threading.Thread(target=inactivity_rotation_watcher, daemon=True)
    watcher_thread.start()
    server = Server()
    while True:
        time.sleep(1)
        pass