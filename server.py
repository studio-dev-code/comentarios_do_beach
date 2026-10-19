import json, os, sqlite3, secrets, hashlib, hmac, time, threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
ROOT=Path(__file__).resolve().parent
DB=ROOT/'data'/'reviews.sqlite3'
DB.parent.mkdir(exist_ok=True)
with sqlite3.connect(DB) as db:
    db.execute('CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP, rating INTEGER NOT NULL, meal TEXT NOT NULL, name TEXT NOT NULL, comment TEXT NOT NULL)')
    cols={r[1] for r in db.execute('PRAGMA table_info(reviews)')}
    for col,definition in [('status',"TEXT NOT NULL DEFAULT 'pending'"),('receipt','TEXT'),('publication_consent','INTEGER NOT NULL DEFAULT 0'),('consent_at','TEXT'),('consent_version','TEXT'),('food_rating','INTEGER'),('service_rating','INTEGER'),('wait_rating','INTEGER'),('ambience_rating','INTEGER'),('wait_not_applicable','INTEGER NOT NULL DEFAULT 0')]:
        if col not in cols: db.execute('ALTER TABLE reviews ADD COLUMN '+col+' '+definition)
    db.execute("UPDATE reviews SET status='private' WHERE publication_consent=0")
    db.execute('CREATE UNIQUE INDEX IF NOT EXISTS receipt_idx ON reviews(receipt)')
SESSIONS={}
ATTEMPTS={}
LOCK=threading.Lock()
def password_hash(password,salt):
    return hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()
class Handler(BaseHTTPRequestHandler):
    def respond(self,code,data,mime='application/json; charset=utf-8',cookie=None):
        body=data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False).encode()
        self.send_response(code)
        for k,v in [('Content-Type',mime),('Content-Length',str(len(body))),('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),('Referrer-Policy','no-referrer'),('X-Frame-Options','DENY')]: self.send_header(k,v)
        if cookie: self.send_header('Set-Cookie',cookie)
        self.end_headers()
        self.wfile.write(body)
    def admin(self):
        try:
            cookies=SimpleCookie(self.headers.get('Cookie',''))
            token=cookies['beach_session'].value
            with LOCK:
                now=time.time()
                for key in list(SESSIONS):
                    if SESSIONS[key]<now: del SESSIONS[key]
                return token in SESSIONS
        except (KeyError,ValueError): return False
    def rows(self,where,args=(),detailed=False):
        with sqlite3.connect(DB) as db:
            db.row_factory=sqlite3.Row
            fields='id,created_at,rating,meal,name,comment,status,publication_consent,consent_at,consent_version'
            if detailed: fields+=',food_rating,service_rating,wait_rating,ambience_rating,wait_not_applicable'
            return [dict(r) for r in db.execute('SELECT '+fields+' FROM reviews WHERE '+where+' ORDER BY id DESC LIMIT 200',args)]
    def do_GET(self):
        path=self.path.split('?')[0]
        pages={'/':'index.html','/index.html':'index.html','/avaliacoes':'reviews.html','/admin':'admin.html'}
        if path in pages: return self.respond(200,(ROOT/pages[path]).read_bytes(),'text/html; charset=utf-8')
        if path=='/api/reviews': return self.respond(200,self.rows("status='approved' AND publication_consent=1"))
        if path=='/api/admin/session': return self.respond(200,{'authenticated':self.admin(),'configured':(ROOT/'data'/'admin.json').exists()})
        if path=='/api/admin/stats':
            if not self.admin(): return self.respond(401,{'error':'Entre no painel.'})
            with sqlite3.connect(DB) as db:
                stats={}
                for field in ('rating','food_rating','service_rating','wait_rating','ambience_rating'):
                    avg,count=db.execute('SELECT AVG('+field+'),COUNT('+field+') FROM reviews').fetchone()
                    stats[field]={'average':round(avg,2) if avg is not None else None,'count':count}
            return self.respond(200,stats)
        if path=='/api/admin/reviews':
            if not self.admin(): return self.respond(401,{'error':'Entre no painel.'})
            return self.respond(200,self.rows('1=1',detailed=True))
        self.respond(404,{})
    def do_POST(self):
        try:
            if self.headers.get('X-Requested-With')!='BeachHills': return self.respond(403,{})
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=12000: return self.respond(413,{})
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict): return self.respond(400,{})
            if self.path=='/api/reviews':
                rating,meal=data.get('rating'),data.get('meal')
                name,comment=data.get('name',''),data.get('comment','')
                if type(rating) is not int or rating not in range(1,6) or meal not in ('Café da manhã','Almoço','Jantar') or not isinstance(name,str) or not isinstance(comment,str) or len(name)>80 or len(comment)>1500: return self.respond(400,{'error':'Confira os campos.'})
                categories=[data.get(k) for k in ('food_rating','service_rating','wait_rating','ambience_rating')]
                if any(v is not None and (type(v) is not int or v not in range(1,6)) for v in categories): return self.respond(400,{'error':'As notas devem estar entre 1 e 5.'})
                wait_na=data.get('wait_not_applicable',False)
                if type(wait_na) is not bool or (wait_na and categories[2] is not None): return self.respond(400,{'error':'Confira a avaliação do tempo de espera.'})
                consent=data.get('publication_consent',False)
                if type(consent) is not bool: return self.respond(400,{})
                token=secrets.token_urlsafe(32)
                with sqlite3.connect(DB) as db:
                    cursor=db.execute('INSERT INTO reviews (rating,meal,name,comment,receipt,publication_consent,consent_at,consent_version,status,food_rating,service_rating,wait_rating,ambience_rating,wait_not_applicable) VALUES (?,?,?,?,?,?,CASE WHEN ?=1 THEN CURRENT_TIMESTAMP ELSE NULL END,?,?,?,?,?,?,?)',(rating,meal,name.strip().split(' ')[0],comment.strip(),hashlib.sha256(token.encode()).hexdigest(),int(consent),int(consent),'publication-v1' if consent else None,'pending' if consent else 'private',*categories,int(wait_na)))
                    review_id=cursor.lastrowid
                return self.respond(201,{'ok':True,'id':review_id,'receipt':token})
            if self.path=='/api/reviews/own':
                token=data.get('receipt','')
                if not isinstance(token,str) or len(token)>100: return self.respond(400,{})
                return self.respond(200,self.rows('receipt=?',(hashlib.sha256(token.encode()).hexdigest(),)))
            if self.path=='/api/admin/login':
                ip=self.client_address[0]
                with LOCK:
                    recent=[t for t in ATTEMPTS.get(ip,[]) if t>time.time()-300]
                    if len(recent)>=5: return self.respond(429,{'error':'Muitas tentativas. Aguarde 5 minutos.'})
                    ATTEMPTS[ip]=recent+[time.time()]
                config=ROOT/'data'/'admin.json'
                if not config.exists(): return self.respond(503,{'error':'Administrador ainda não configurado. Execute python3 setup_admin.py no terminal.'})
                auth=json.loads(config.read_text())
                username,password=data.get('username',''),data.get('password','')
                if not isinstance(password,str) or len(password)>256: return self.respond(400,{})
                valid=hmac.compare_digest(password_hash(password,auth['salt']),auth['hash'])
                if not valid or username!=auth['username']: return self.respond(401,{'error':'Usuário ou senha incorretos.'})
                token=secrets.token_urlsafe(32)
                with LOCK:
                    SESSIONS[token]=time.time()+8*3600
                    ATTEMPTS.pop(ip,None)
                secure='; Secure' if self.headers.get('X-Forwarded-Proto')=='https' else ''
                return self.respond(200,{'ok':True},cookie='beach_session='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800'+secure)
            if self.path.startswith('/api/admin/'):
                if not self.admin(): return self.respond(401,{'error':'Entre no painel.'})
                if self.path=='/api/admin/logout':
                    cookies=SimpleCookie(self.headers.get('Cookie',''))
                    with LOCK: SESSIONS.pop(cookies['beach_session'].value,None)
                    return self.respond(200,{'ok':True},cookie='beach_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
                if self.path=='/api/admin/moderate':
                    review_id,status=data.get('id'),data.get('status')
                    if type(review_id) is not int or status not in ('approved','rejected','pending'): return self.respond(400,{})
                    with sqlite3.connect(DB) as db:
                        row=db.execute('SELECT publication_consent FROM reviews WHERE id=?',(review_id,)).fetchone()
                        if row and not row[0]: return self.respond(409,{'error':'Sem autorização do hóspede: esta avaliação deve permanecer privada.'})
                        changed=db.execute('UPDATE reviews SET status=? WHERE id=?',(status,review_id)).rowcount
                    return self.respond(200 if changed else 404,{'ok':bool(changed)})
            self.respond(404,{})
        except (ValueError,TypeError,AttributeError): self.respond(400,{})
        except (sqlite3.Error,OSError): self.respond(503,{'error':'Serviço temporariamente indisponível.'})
if __name__=='__main__':
    print('Beach Hills na porta '+os.environ.get('PORT','8000'),flush=True)
    ThreadingHTTPServer(('0.0.0.0',int(os.environ.get('PORT','8000'))),Handler).serve_forever()
