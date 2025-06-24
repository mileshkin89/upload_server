# server.py
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import uuid
import json
from urllib.parse import unquote

UPLOAD_DIR = "./images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class UploadHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Определяем путь
        route = unquote(self.path)

        # Не работают иконки в "image.html"
        # # 1. Отображение страницы просмотра отдельного изображения
        # if route.startswith("/images/") and any(route.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif"]):
        #     # Вместо того чтобы отдавать сам файл — отдаем HTML с встраиванием
        #     self.serve_image_page(route.split("/images/")[1])
        # # 2. Галерея
        # elif route == "/images":
        #     self.serve_html("images.html")
        # # 3. Отдача остальных HTML-страниц
        # elif route in ["/", "/index.html"]:
        #     self.serve_html("index.html")
        # elif route == "/upload":
        #     self.serve_html("upload.html")
        # # 4. API
        # elif route == "/api/images":
        #     self.serve_storage("images")
        # # 5. Статика
        # elif route.startswith("/css/") or route.startswith("/js/") or route.startswith("/random_images/"):
        #     self.serve_static(route[1:])
        # # 6. Если ничего не подошло — ошибка
        # else:
        #     self.send_error(404, f"Page not found: {route}")

        # Не работает "user_image.html"
        # 1. Отдача загружаемых изображений (например, /images/abc.jpg)
        if route.startswith("/images/") and any(route.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif"]):
            self.serve_static(route[1:])
        # 2. Страница с отдельным просмотром изображения (например, /images/abc123.jpg)
        elif route.startswith("/images/"):
            self.serve_image_page(route.split("/images/")[1])
        # 3. HTML-страницы
        elif route in ["/", "/index.html"]:
            self.serve_html("index.html")
        elif route == "/images":
            self.serve_html("images.html")
        elif route == "/upload":
            self.serve_html("upload.html")
        # 4. API: список изображений
        elif route == "/api/images":
            self.serve_storage("images")
        # 5. Остальная статика (CSS, JS и пр.)
        elif route.startswith("/css/") or route.startswith("/js/") or route.startswith("/random_images/"):
            self.serve_static(route[1:])
        # 6. Если ничего не подошло — ошибка
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
                content_type = "image/png"
            elif filepath.endswith(".jpg") or filepath.endswith(".jpeg"):
                content_type = "image/jpeg"
            elif filepath.endswith(".gif"):
                content_type = "image/gif"
            else:
                content_type = "application/octet-stream"

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, f"Static file not found: {filepath}")

    def serve_storage(self, filepath):
        try:
            files = os.listdir(filepath)
            # Оставляем только изображения
            images = [f for f in files if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(images).encode())
        except Exception as e:
            self.send_error(500, f"Error reading image directory: {e}")

    def serve_image_page(self, filename):
        filepath = os.path.join(UPLOAD_DIR, filename)
        abs_path = os.path.abspath(filepath)

        if not abs_path.startswith(os.path.abspath(UPLOAD_DIR)) or not os.path.isfile(abs_path):
            self.send_error(404, f"Image {filename} not found or invalid path")
            return

        try:
            with open("user_image.html", "r", encoding="utf-8") as f:
                html = f.read()
        except FileNotFoundError:
            self.send_error(404, f"{filename} not found")
            return

        html = html.replace("{filename}", filename)

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


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


    def do_DELETE(self):
        route = unquote(self.path)
        if route.startswith("/api/images/"):
            filename = route.split("/api/images/")[1]
            filepath = os.path.join(UPLOAD_DIR, filename)

            if os.path.exists(filepath):
                os.remove(filepath)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"File deleted")
            else:
                self.send_error(404, "File not found")
        else:
            self.send_error(404, "Invalid DELETE route")


if __name__ == "__main__":
    try:
        server = HTTPServer(("localhost", 8000), UploadHandler)
        print("Upload server running on http://localhost:8000")
        server.serve_forever()
    except Exception:
        server.shutdown()



