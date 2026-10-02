#!/usr/bin/env python3
"""Лёгкий статик-сервер с поддержкой HTTP Range (нужно для аудио в Safari)."""
import os
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PORT = 8000


class RangeHTTPRequestHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        range_header = self.headers.get("Range")
        path = self.translate_path(self.path)

        if not (range_header and os.path.isfile(path)):
            return super().send_head()

        m = re.match(r"bytes=(\d*)-(\d*)", range_header)
        if not m:
            return super().send_head()

        file_size = os.path.getsize(path)
        start = int(m.group(1) or 0)
        end = int(m.group(2) or file_size - 1)
        end = min(end, file_size - 1)

        if start > end:
            self.send_error(416, "Requested Range Not Satisfiable")
            return None

        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Last-Modified", self.date_time_string())
        self.end_headers()

        f = open(path, "rb")
        f.seek(start)
        self._chunked = f.read(end - start + 1)
        return f

    def copyfile(self, source, outputfile):
        if hasattr(self, "_chunked") and self._chunked is not None:
            outputfile.write(self._chunked)
            self._chunked = None
        else:
            super().copyfile(source, outputfile)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), RangeHTTPRequestHandler)
    print(f"Сервер на http://127.0.0.1:{PORT}/")
    server.serve_forever()