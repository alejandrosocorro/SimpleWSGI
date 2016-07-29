import os
import sys
import time
import socket
import StringIO


class SimpleWSGI(object):

    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 1

    def __init__(self, server_address):
        # Create listening socket
        self.listen_socket = listen_socket = socket.socket(
            self.address_family,
            self.socket_type
        )
        # Set socket options. Reuse the same address
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind server address
        listen_socket.bind(server_address)
        # listen with a max queue size
        listen_socket.listen(self.request_queue_size)
        # Server HOST and PORT
        host, port = self.listen_socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port
        # Headers set by Web framework/Web application
        self.headers_set = []

    def set_app(self, application):
        self.application = application

    def serve(self):
        listen_socket = self.listen_socket
        while True:
            self.client_connection, client_address = listen_socket.accept()
            self.handle_request()

    def handle_request(self):
        self.request_data = request_data = self.client_connection.recv(1024)
        # Print formatted request data
        print(''.join(
            '< {line}\n'.format(line=line)
            for line in request_data.splitlines()
        ))

        self.parse_request(request_data)
        # Construct environment dictionary using request data
        env = self.get_environ()
        # Call oapplication callable
        result = self.application(env, self.start_response)
        # Construct a response and send it back to the client
        self.response(result)

    def parse_request(self, text):
        request_line = text.splitlines()[0]
        request_line = request_line.rstrip('\r\n')
        (self.request_method,  # GET
         self.path,            # /hello
         self.request_version  # HTTP/1.1
         ) = request_line.split()

    def get_environ(self):
        environ = dict(os.environ.items())
        environ['wsgi.version']      = (1, 0)
        #environ['wsgi.input']        = sys.stdin
        environ['wsgi.input']        = StringIO.StringIO(self.request_data),
        environ['wsgi.errors']       = sys.stderr
        environ['wsgi.version']      = (1, 0)
        environ['wsgi.multithread']  = False
        environ['wsgi.multiprocess'] = True
        environ['wsgi.run_once']     = True
        environ['REQUEST_METHOD']    = self.request_method
        environ['PATH_INFO']         = self.path
        environ['SERVER_NAME']       = self.server_name
        environ['SERVER_PORT']       = str(self.server_port)

        if env.get('HTTPS', 'off') in ('on', '1'):
            env['wsgi.url_scheme'] = 'https'
        else:
            env['wsgi.url_scheme'] = 'http'

        return env


SERVER_ADDRESS = (HOST, PORT) = '', 8888


def make_server(server_address, application):
    server = WSGIServer(server_address)
    server.set_app(application)
    return server


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Provide a WSGI application object as module:callable')
    app_path = sys.argv[1]
    module, application = app_path.split(':')
    module = __import__(module)
    application = getattr(module, application)
    httpd = make_server(SERVER_ADDRESS, application)
    print('SimpleWSGI: Serving HTTP on port {port} ...\n'.format(port=PORT))
    httpd.serve()
