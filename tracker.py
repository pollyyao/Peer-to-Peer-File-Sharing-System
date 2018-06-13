import socket, sys, threading, json, time, optparse, os


def validate_ip(s):
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True


def validate_port(x):
    if not x.isdigit():
        return False
    i = int(x)
    if i < 0 or i > 65535:
        return False
    return True


class Tracker(threading.Thread):
    def __init__(self, port, host='0.0.0.0'):
        threading.Thread.__init__(self)
        self.port = port
        self.host = host
        self.BUFFER_SIZE = 8192
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.users = {}  # current connections  self.users[(ip,port)] = {'exptime':}
        self.files = {}  # {'ip':,'port':,'mtime':}
        self.lock = threading.Lock()
        try:
            # YOUR CODE
            # Bind to address and port
            self.server.bind((self.host, self.port))

        except socket.error:
            print('Bind failed %s' % (socket.error))
            sys.exit()
            # YOUR CODE
            # listen for connections
            # become a server socket
            # the argument to listen tells the socket library that we want it to queue up as many as 5 connect requests
            # (the normal max) before refusing outside connections.
        self.server.listen(5)


    def check_user(self):

    # YOUR CODE
    # checking users are alive
    # current connections  self.users[(ip,port)] = {'exptime':}
        for key, value in self.users.items():
            ip = key[0]
            port = key[1]
            exptime = value
            # remove entries of the files associated with the peer
            if (exptime < 0):
                self.lock.acquire()
                print 'delete user:', self.users[key]
                del self.users[key]
                self.lock.release()
                for k, v in self.files.items():
                    # {'ip':,'port':,'mtime':}
                    if (v[1] == port):
                        self.lock.acquire()
                        print 'delete file:', self.files[k]
                        del self.files[k]
                        self.lock.release()
            else:
                self.users[key] = exptime - 5.0

        threading.Timer(5.0, self.check_user).start()

    # Ensure sockets are closed on disconnect
    def exit(self):
        self.server.close()

    def run(self):
        print('Waiting for connections on port %s' % (self.port))
        while True:
            # YOUR CODE
            # accept incoming connection and create a thread for receiving messages from FileSynchronizer
            # accept connections from outside
            conn, addr = self.server.accept()
            print 'Connected by ' + addr[0] + ':' + str(addr[1])

            threading.Thread(target=self.proces_messages, args=(conn, addr)).start()

    def proces_messages(self, conn, addr):
        conn.settimeout(180.0)
        # ip = addr[0]
        print 'Client connected with ' + addr[0] + ':' + str(addr[1])
        while True:
            # recive data
            data = ''
            while True:
                part = conn.recv(self.BUFFER_SIZE)
                data = data + part
                if len(part) < self.BUFFER_SIZE:
                    break
            # YOUR CODE
            # check if the received data is a json string and load the json string
            try:
                # transfer string to dict
                data_dic = json.loads(data)
                print 'data_dic: ', data_dic
            except ValueError:
                print('Invalid Json String: %s' % ValueError)

            # sync and send files json data
            fileport = data_dic['port']
            for file in data_dic['files']:
                filename = file['name']
                filemtime = file['mtime']
                fileip = addr[0]
                self.lock.acquire()
                self.files[filename] = {'ip': fileip, 'port': fileport, 'mtime': filemtime}
                self.lock.release()
            # transfer json dict to string
            data_out = json.dumps(self.files)
            # send all data
            conn.sendall(data_out)

        conn.close()  # Close


if __name__ == '__main__':
    parser = optparse.OptionParser(usage="%prog ServerIP ServerPort")
    options, args = parser.parse_args()
    if len(args) < 1:
        parser.error("No ServerIP and ServerPort")
    elif len(args) < 2:
        parser.error("No ServerIP or ServerPort")
    else:
        if validate_ip(args[0]) and validate_port(args[1]):
            server_ip = args[0]
            server_port = int(args[1])
        else:
            parser.error("Invalid ServerIP or ServerPort")
    tracker = Tracker(server_port, server_ip)
    tracker.start()
