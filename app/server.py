"""Read-only synthetic dispatch register; loopback only."""
import argparse
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3


def orders(database):
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as con:
        rows = con.execute('SELECT id, reference, status FROM orders ORDER BY id').fetchall()
    return [dict(zip(('id', 'reference', 'status'), row)) for row in rows]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            records = orders(self.server.database)
            if self.path == '/health':
                payload = {'status': 'ok', 'orders': len(records), 'site': self.server.site}
            elif self.path == '/orders':
                payload = {'orders': records}
            else:
                self.send_error(404)
                return
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(body)
        except (OSError, sqlite3.Error):
            self.send_error(503, 'Dataset unavailable')

    def log_message(self, format, *args):
        print('request status=' + str(args[1]), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--port', type=int, default=18765)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.database = args.database.resolve()
    config = json.loads(args.config.read_text())
    if config.get('mode') != 'dispatch':
        raise ValueError('Unsupported operational mode')
    server.site = config['site']
    server.serve_forever()


if __name__ == '__main__':
    main()
