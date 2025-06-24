# from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler
# from http.server import HTTPServer
#
# class HttpGetHandler(BaseHTTPRequestHandler):
#     """Обработчик с реализованным методом do_GET."""
#
#     def do_GET(self):
#         self.send_response(200)
#         self.send_header("Content-type", "text/html")
#         self.end_headers()
#         self.wfile.write('<html><head><meta charset="utf-8">'.encode())
#         self.wfile.write('<title>Простой HTTP-сервер.</title></head>'.encode())
#         self.wfile.write('<body>Был получен GET-запрос.</body></html>'.encode())
#
#
# def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
# #def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler):
#   server_address = ('', 8000)
#   httpd = server_class(server_address, handler_class)
#   try:
#       print("serving at port", 8000)
#       httpd.serve_forever()
#   except KeyboardInterrupt:
#       httpd.server_close()
#
#
# run(handler_class=HttpGetHandler)

# http://localhost:8000/


# ===================================
# import http.server
# import socketserver
#
# PORT = 8000
# Handler = http.server.SimpleHTTPRequestHandler

# with socketserver.TCPServer(("local", PORT), Handler) as httpd:
#     print("serving at port", PORT)
#     httpd.serve_forever()


# ===============================================
from http.server import HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
# from io import BytesIO
#
# class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
#
#     # определяем метод `do_GET`
#     def do_GET(self):
#         self.send_response(200)
#         self.send_header('Content-type', 'text/html')
#         self.end_headers()
#         self.wfile.write(b'Hello, world!')
#
#     # определяем метод `do_POST`
#     def do_POST(self):
#         content_length = int(self.headers['Content-Length'])
#         body = self.rfile.read(content_length)
#         self.send_response(200)
#         self.send_header('Content-type', 'text/html')
#         self.end_headers()
#         response = BytesIO()
#         response.write(b'This is POST request. ')
#         response.write(b'Received: ')
#         response.write(body)
#         self.wfile.write(response.getvalue())


server_address = ('', 8000)
try:
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    httpd.serve_forever()
except Exception:
    httpd.shutdown()



