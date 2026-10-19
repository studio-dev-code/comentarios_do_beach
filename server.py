import json, os, sqlite3
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ROOT = Path(__file__).resolve().parent
DB = ROOT / 'data' / 'reviews.sqlite3'
DB.parent.mkdir(exist_ok=True)
with sqlite3.connect(DB) as db:
    db.execute('CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP, rating INTEGER NOT NULL, meal TEXT NOT NULL, name TEXT NOT NULL, comment TEXT NOT NULL)')
class Handler(BaseHTTPRequestHandler):
    def respond(self, code, body, mime='application/json; charset=utf-8'):
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        if self.path.split('?')[0] in ('/', '/index.html'):
            self.respond(200, (ROOT / 'index.html').read_bytes(), 'text/html; charset=utf-8')
        else:
            self.respond(404, b'{}')
    def do_POST(self):
        if self.path != '/api/reviews':
            return self.respond(404, b'{}')
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 12000:
                return self.respond(413, b'{}')
            data = json.loads(self.rfile.read(length))
            rating, meal = data.get('rating'), data.get('meal')
            name, comment = data.get('name', ''), data.get('comment', '')
            if type(rating) is not int or rating not in range(1,6) or meal not in ('Café da manhã','Almoço','Jantar') or not isinstance(name,str) or not isinstance(comment,str) or len(name)>80 or len(comment)>1500:
                return self.respond(400, b'{}')
            with sqlite3.connect(DB) as db:
                db.execute('INSERT INTO reviews (rating,meal,name,comment) VALUES (?,?,?,?)', (rating,meal,name.strip(),comment.strip()))
            self.respond(201, b'{"ok":true}')
        except (ValueError, TypeError, AttributeError):
            self.respond(400, b'{}')
        except sqlite3.Error:
            self.respond(503, b'{}')
if __name__ == '__main__':
    port=int(os.environ.get('PORT','8000'))
    print(f'Beach Hills: http://0.0.0.0:{port}', flush=True)
    ThreadingHTTPServer(('0.0.0.0',port), Handler).serve_forever()
