# server.py
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import uuid
import json
import shutil
from multipart import parse_form
from PIL import Image, UnidentifiedImageError
from exceptions import APIError, MaxSizeExceedError, MultipleFilesUploadError, NotSupportedFormatError
from settings.config import config
from settings.logging_config import get_logger

logger = get_logger(__name__)

os.makedirs(config.UPLOAD_DIR, exist_ok=True)


class UploadHandler(BaseHTTPRequestHandler):
    routes_get = {
        "/api/images": "_handle_api_images",
        "/images_repo/": "_handle_images_repo",
        "/static/": "_handle_static",
        "/images/": "_handle_get_image_data",
        "/upload": "_handle_get_uploads",
        "/images": "_handle_get_images_list",
        "/": "_handle_get_root",
    }

    routes_post = {
        "/upload": "_handle_post_upload",
    }

    routes_delete = {
        "/api/images/": "_handle_delete_image",
        "/images/": "_handle_delete_image",
    }

    def _send_json_error(self, status_code: int, message: str) -> None:
        """Sends a JSON error response and logs the message.

        Args:
            status_code (int): HTTP status code to return.
            message (str): Error message to return and log.

        Side effects:
            - Logs the error or warning.
            - Writes JSON response to the client.
        """
        if status_code >= 500:
            logger.error(f"{self.command} {self.path} → {status_code}: {message}")
        else:
            logger.warning(f"{self.command} {self.path} → {status_code}: {message}")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = {"detail": message}
        self.wfile.write(json.dumps(response).encode())


    def do_GET(self):
        """Handles GET requests and dispatches them based on route."""
        self._handle_request(self.routes_get)

    def do_POST(self):
        """Handles POST requests and dispatches them based on route."""
        self._handle_request(self.routes_post)

    def do_DELETE(self):
        """Handles DELETE requests and dispatches them based on route."""
        self._handle_request(self.routes_delete)


    def _handle_request(self, routes: dict[str, str]) -> None:
        print("_handle_request//  path = ", self.path)
        handler_name = routes.get(self.path)
        if not handler_name:
            for route_prefix, candidate_handler in routes.items():
                if self.path.startswith(route_prefix):
                    handler_name = candidate_handler
                    print("11 handler name = ", handler_name)
                    break

        if not handler_name:
            self._send_json_error(404, "Not Found")
            return

        handler = getattr(self, handler_name, None)
        if not handler:
            self._send_json_error(500, "Handler not implemented.")
            return

        handler()


    def _serve_html(self, filename):
        full_path = os.path.join(config.FRONTEND_DIR, filename)
        logger.info(f"_serve_html full_path = {full_path}")
        try:
            with open(full_path, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, f"{filename} not found")
            self._send_json_error(404, f"{filename} not found")


    def _serve_static(self, filepath: str, repo: str = config.FRONTEND_DIR):
        full_path = os.path.join(repo, filepath)
        logger.info(f"_serve_static full_path = {full_path}")
        if not os.path.isfile(full_path):
            self._send_json_error(404, f"Static file not found: {filepath}")
            return

        try:
            with open(full_path, "rb") as f:
                content = f.read()

            # Content-Type
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
        except Exception as e:
            self._send_json_error(500, f"Error reading static file: {e}")

    def _serve_storage(self, filepath):
        try:
            files = os.listdir(filepath)
            # Оставляем только изображения
            images = [f for f in files if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            print("_serve_storage images = ", images)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(images).encode())
        except Exception as e:
            self.send_error(500, f"Error reading image directory: {e}")


    def _handle_images_repo(self):
        print("_handle_images_repo  self.path = ", self.path)
        if self.path.startswith("/images_repo/") and any(self.path.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif"]):
            filepath = self.path[len("/images_repo/"):]
            self._serve_static(filepath, config.UPLOAD_DIR)


    def _handle_static(self):
        self._serve_static(self.path.lstrip("/"))

    def _handle_api_images(self):
        self._serve_storage(config.UPLOAD_DIR)


    def _handle_get_root(self):
        self._serve_html("index.html")

    def _handle_get_uploads(self):
        self._serve_html("upload.html")

    def _handle_get_images_list(self):
        self._serve_html("images.html")

    def _handle_get_image_data(self):
        self._serve_html("image_data.html")



    def _handle_post_upload(self):
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._send_json_error(400, "Bad Request: Expected multipart/form-data")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        headers = {
            "Content-Type": content_type,
            "Content-Length": str(content_length)
        }

        files = []

        def on_file(file):
            if len(files) >= 1:
                raise MultipleFilesUploadError()
            files.append(file)

        try:
            parse_form(headers, self.rfile, lambda _: None, on_file)  # type: ignore[arg-type]
        except APIError as e:
            self._send_json_error(e.status_code, e.message)
            return

        file = files[0]

        filename = file.file_name.decode("utf-8") if file.file_name else "uploaded_file"
        ext = os.path.splitext(filename)[1].lower()

        if ext not in config.SUPPORTED_FORMATS:
            raise NotSupportedFormatError(config.SUPPORTED_FORMATS)

        file.file_object.seek(0, os.SEEK_END)
        size = file.file_object.tell()
        file.file_object.seek(0)

        if size > config.MAX_FILE_SIZE:
            raise MaxSizeExceedError(config.MAX_FILE_SIZE)

        try:
            image = Image.open(file.file_object)
            image.verify()
            file.file_object.seek(0)
        except (UnidentifiedImageError, OSError):
            raise NotSupportedFormatError(config.SUPPORTED_FORMATS)

        original_name = os.path.splitext(filename)[0].lower()
        unique_name = f"{original_name}_{uuid.uuid4()}{ext}"

        os.makedirs(config.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(config.UPLOAD_DIR, unique_name)

        with open(file_path, "wb") as f:
            file.file_object.seek(0)
            shutil.copyfileobj(file.file_object, f)

        url = f"/images/{unique_name}"

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(
            f'{{"filename": "{unique_name}", '
            f'"url": "{url}"}}'.encode()
        )



    def _delete_image(self, filepath):
        if filepath.startswith("/api/images/"):
            filename = filepath[len("/api/images/"):]
        elif filepath.startswith("/images/"):
            filename = filepath[len("/images/"):]

        if not filename:
            self._send_json_error(400, "Filename not provided.")
            return

        filepath = os.path.join(config.UPLOAD_DIR, filename)
        ext = os.path.splitext(filename)[1].lower()

        if ext not in config.SUPPORTED_FORMATS:
            self._send_json_error(400, "Unsupported file format.")
            return

        if not os.path.isfile(filepath):
            self._send_json_error(404, "File not found.")
            return

        try:
            os.remove(filepath)
        except PermissionError:
            self._send_json_error(500, "Permission denied to delete file.")
            return
        except Exception as e:
            self._send_json_error(500, f"Internal Server Error: {str(e)}")
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"message": f"File '{filename}' deleted successfully."}).encode())


    def _handle_delete_image(self):
        print("_handle_delete_image  self.path = ", self.path)
        self._delete_image(self.path)




if __name__ == "__main__":
    try:
        server = HTTPServer(("localhost", 8000), UploadHandler)
        print("Upload server running on http://localhost:8000")
        server.serve_forever()
    except Exception:
        server.shutdown()



