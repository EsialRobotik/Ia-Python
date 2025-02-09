import socket
import threading
import time
import pickle
import logging
import logging.handlers
import socketserver
import struct
import sys

log_listener = None

class Server:
    def __init__(self):
        self.robots = []
        
        self.init_communication_server()
        self.tcpserver = LogRecordSocketReceiver()
        print('About to start TCP server...')
        self.tcpserver.serve_until_stopped()

    def init_communication_server(self):
        self.communication_server_socket = socket.socket()
        self.communication_server_socket.bind(('', 4269)) # empty host allow any ip to connect
        self.communication_server_socket.listen(10)
        comm_connection_thread = threading.Thread(target=self.accept_communication_connection)
        comm_connection_thread.daemon = True
        comm_connection_thread.start()

    def accept_communication_connection(self):
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
    """Handler for a streaming logging request.

    This basically logs the record using whatever logging policy is
    configured locally.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """

        global log_listener
        file_handler = logging.handlers.RotatingFileHandler(filename='logs/server-log.log', backupCount=50)
        file_handler.doRollover()
        stdout_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stdout_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(stdout_handler)
        logging.getLogger().addHandler(file_handler)
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
            if log_listener != None:
                log_listener.send(formatter.format(record).encode())

    def unPickle(self, data):
        return pickle.loads(data)

class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
    Simple TCP socket-based logging receiver suitable for testing.
    """

    allow_reuse_address = True

    def __init__(self, host='',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 handler=LogRecordStreamHandler):
        socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1
        self.logname = None

    def serve_until_stopped(self):
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
    server = Server()
    while True:
        time.sleep(1)
        pass