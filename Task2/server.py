import socket
import os
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import logging

# Logger setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set base directory for server
BASE_DIR = Path(__file__).parent

def get_content_type(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    return {
        '.html': 'text/html; charset=utf-8',
        '.css': 'text/css',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.mp4': 'video/mp4',
        '.ico': 'image/x-icon'
    }.get(ext, 'application/octet-stream')

def generate_response(file_path, client_address):
    if file_path == "favicon.ico":
        return b"HTTP/1.1 204 No Content\r\n\r\n"

    # Determine folder based on file type
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".html":
        abs_path = BASE_DIR / "html" / file_path
    elif ext == ".css":
        abs_path = BASE_DIR / "css" / file_path
    elif ext in [".jpg", ".jpeg", ".png"]:
        abs_path = BASE_DIR / "images" / file_path
    elif ext == ".mp4":
        abs_path = BASE_DIR / "video" / file_path
    else:
        abs_path = BASE_DIR / file_path

    logger.debug(f"Looking for file: {abs_path}")

    if abs_path.exists() and abs_path.is_file():
        content_type = get_content_type(file_path)
        
        # Set appropriate headers for direct streaming
        header = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\n"
        if ext in ['.mp4', '.jpg', '.jpeg', '.png']:
            # Instruct the browser to display the content directly (no download)
            header += "Content-Disposition: inline\r\n"
        header += "\r\n"

        with open(abs_path, 'rb') as f:
            content = f.read()
        return header.encode() + content
    else:
        logger.warning(f"File not found: {abs_path}")
        # Redirect to Google search for missing content
        return handle_redirect(file_path, 'image' if ext in ['.jpg', '.jpeg', '.png'] else 'video')

def handle_redirect(query, file_type):
    if file_type == 'image':
        url = f"https://www.google.com/search?hl=en&tbm=isch&q={query}"
    elif file_type == 'video':
        url = f"https://www.google.com/search?hl=en&tbm=vid&q={query}"
    else:
        return None
    return f"HTTP/1.1 307 Temporary Redirect\r\nLocation: {url}\r\n\r\n".encode()

def handle_request(request_data, client_address):
    try:
        lines = request_data.split('\r\n')
        if not lines:
            return None
        request_line = lines[0]
        logger.debug(f"Request line: {request_line}")
        parts = request_line.split()
        if len(parts) < 2:
            return None
        method, full_path = parts[0], parts[1]
        parsed = urlparse(full_path)
        path = parsed.path.lstrip('/')
        query_params = parse_qs(parsed.query)

        if 'file-request' in query_params:
            filename = query_params['file-request'][0]
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                return generate_response(filename, client_address)
            elif ext == '.mp4':
                return generate_response(filename, client_address)
            else:
                return generate_response(filename, client_address)

        if path in ['', 'index.html', 'en', 'main_en.html']:
            path = 'main_en.html'
        elif path in ['ar', 'main_ar.html']:
            path = 'main_ar.html'
        elif 'mySite_1222192_en.html' in path:
            path = 'mySite_1222192_en.html'
        elif 'mySite_1222192_ar.html' in path:
            path = 'mySite_1222192_ar.html'

        logger.debug(f"Resolved path: {path}")
        return generate_response(path, client_address)

    except Exception as e:
        logger.error(f"Error: {e}")
        return b"HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\n\r\n" \
               b"<html><body><h1>500 Internal Server Error</h1></body></html>"

def start_server():
    host = '127.0.0.1'
    port = 9912  # based on ID 1222192

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)

    logger.info(f"Server started on {host}:{port}")

    try:
        while True:
            client_socket, client_address = server.accept()
            logger.info(f"Connection from {client_address}")
            try:
                request = client_socket.recv(1024).decode()
                if not request:
                    continue
                logger.debug(f"Request received:\n{request}")
                response = handle_request(request, client_address)
                if response:
                    client_socket.sendall(response)
            except Exception as e:
                logger.error(f"Client error: {e}")
            finally:
                client_socket.close()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    finally:
        server.close()

if __name__ == "__main__":  # Corrected this line
    start_server()
