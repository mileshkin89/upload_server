from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import uuid
from urllib.parse import unquote

UPLOAD_DIR = "./images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class UploadHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Определяем путь
        route = unquote(self.path)

        # Роутинг для HTML-страниц
        if route == "/" or route == "/index.html":
            self.serve_html("index.html")
        elif route == "/images":
            self.serve_html("images.html")
        elif route == "/upload":
            self.serve_html("upload.html")
        # Обработка статики: CSS, JS, картинки
        elif route.startswith("/css/") or route.startswith("/js/") or route.startswith("/images/"):
            self.serve_static(route[1:])  # Убираем ведущий /
        elif route.startswith("/random_images/"):
            self.serve_static(route[1:])
        else:
            self.send_error(404, f"Page not found: {route}")

    def serve_html(self, filename):
        try:
            with open(filename, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, f"{filename} not found")

    def serve_static(self, filepath):
        try:
            with open(filepath, "rb") as f:
                content = f.read()

            # Определим Content-Type по расширению
            if filepath.endswith(".css"):
                content_type = "text/css"
            elif filepath.endswith(".js"):
                content_type = "application/javascript"
            elif filepath.endswith(".png"):
                content_type = "images/png"
            elif filepath.endswith(".jpg") or filepath.endswith(".jpeg"):
                content_type = "images/jpeg"
            elif filepath.endswith(".gif"):
                content_type = "images/gif"
            else:
                content_type = "application/octet-stream"

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, f"Static file not found: {filepath}")

    def do_POST(self):
        content_type = self.headers.get("Content-Type")
        if not content_type.startswith("multipart/form-data"):
            self.send_error(400, "Content-Type must be multipart/form-data")
            return

        # Определим границу (boundary)
        boundary = content_type.split("boundary=")[1].encode()
        remainbytes = int(self.headers["Content-Length"])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if boundary not in line:
            self.send_error(400, "Content does not begin with boundary")
            return

        # Пропустим заголовки части
        line = self.rfile.readline()
        remainbytes -= len(line)
        disposition = line.decode()
        filename = None
        if 'filename="' in disposition:
            filename = disposition.split('filename="')[1].split('"')[0]
        filepath = os.path.join(UPLOAD_DIR, filename)

        # Пропустим Content-Type
        line = self.rfile.readline()
        remainbytes -= len(line)

        # Пропустим пустую строку
        line = self.rfile.readline()
        remainbytes -= len(line)

        # Генерируем уникальное имя файла
        ext = os.path.splitext(filename)[1] if filename else ".bin"
        unique_name = f"{uuid.uuid4().hex}{ext}"

        # Читаем содержимое файла до следующего boundary
        file_data = b""
        preline = self.rfile.readline()
        remainbytes -= len(preline)
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary in line:
                file_data += preline[:-2]  # remove trailing \r\n
                break
            file_data += preline
            preline = line

        # Сохраняем файл
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        with open(os.path.join(UPLOAD_DIR, unique_name), 'wb') as f:
            f.write(file_data)

        # Возвращаем JSON с именем файла
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = f'{{"filename": "{unique_name}"}}'
        self.wfile.write(response.encode())


if __name__ == "__main__":
    try:
        server = HTTPServer(("localhost", 8000), UploadHandler)
        print("Upload server running on http://localhost:8000")
        server.serve_forever()
    except Exception:
        server.shutdown()



