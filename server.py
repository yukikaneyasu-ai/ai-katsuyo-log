"""
AI活用ログ ローカルサーバー
ブラウザで index.html を直接開くと articles.json を読み込めないため、
このスクリプトで簡易サーバーを起動してから表示します。
Python標準ライブラリのみを使用（pip install不要）。
"""
import http.server
import socketserver
import socket
import webbrowser
import os

DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        pass  # コンソールを静かに保つ


def find_free_port(start=8000, tries=50):
    port = start
    for _ in range(tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", port)) != 0:
                return port
        port += 1
    return start


if __name__ == "__main__":
    port = find_free_port(8000)
    url = f"http://localhost:{port}/index.html"
    print("=" * 50)
    print("AI活用ログ を起動しています")
    print(url)
    print("終了するには このウィンドウで Ctrl+C を押してください。")
    print("=" * 50)
    webbrowser.open(url)
    with socketserver.TCPServer(("", port), Handler) as httpd:
        httpd.serve_forever()
