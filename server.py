import json, os, sqlite3, secrets, hashlib, hmac, time, threading, datetime
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from urllib.parse import urlparse, parse_qs
ROOT=Path(__file__).resolve().parent
DB=ROOT/'data'/'reviews.sqlite3'
DB.parent.mkdir(exist_ok=True)
with sqlite3.connect(DB) as db:
    db.execute('CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP, rating INTEGER NOT NULL, meal TEXT NOT NULL, name TEXT NOT NULL, comment TEXT NOT NULL)')
    cols={r[1] for r in db.execute('PRAGMA table_info(reviews)')}
    for col,definition in [('status',"TEXT NOT NULL DEFAULT 'pending'"),('receipt','TEXT'),('publication_consent','INTEGER NOT NULL DEFAULT 0'),('consent_at','TEXT'),('consent_version','TEXT'),('food_rating','INTEGER'),('service_rating','INTEGER'),('wait_rating','INTEGER'),('ambience_rating','INTEGER'),('wait_not_applicable','INTEGER NOT NULL DEFAULT 0'),('submission_id','TEXT'),('hotel',"TEXT NOT NULL DEFAULT 'beach_hills'")]:
        if col not in cols: db.execute('ALTER TABLE reviews ADD COLUMN '+col+' '+definition)
    db.execute("UPDATE reviews SET status='private' WHERE publication_consent=0")
    db.execute('CREATE UNIQUE INDEX IF NOT EXISTS receipt_idx ON reviews(receipt)')
SESSIONS={}
ATTEMPTS={}
LOCK=threading.Lock()
def password_hash(password,salt):
    return hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()
def load_users():
    path=ROOT/'data'/'users.json'
    if path.exists(): return json.loads(path.read_text())
    legacy=ROOT/'data'/'admin.json'
    if legacy.exists():
        account=json.loads(legacy.read_text())
        return {account['username'].casefold():{'display_name':account['username'],'salt':account['salt'],'hash':account['hash']}}
    return {}
def save_users(users):
    path=ROOT/'data'/'users.json'
    temporary=path.with_name('.users-'+secrets.token_hex(8)+'.tmp')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,'w') as file:
            json.dump(users,file)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary,path)
    finally:
        if temporary.exists(): temporary.unlink()
class Handler(BaseHTTPRequestHandler):
    def respond(self,code,data,mime='application/json; charset=utf-8',cookie=None):
        body=data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False).encode()
        self.send_response(code)
        for k,v in [('Content-Type',mime),('Content-Length',str(len(body))),('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),('Referrer-Policy','no-referrer'),('X-Frame-Options','DENY')]: self.send_header(k,v)
        if cookie: self.send_header('Set-Cookie',cookie)
        self.end_headers()
        self.wfile.write(body)
    def session_info(self):
        try:
            cookies=SimpleCookie(self.headers.get('Cookie',''))
            token=cookies['beach_session'].value
            with LOCK:
                now=time.time()
                for key in list(SESSIONS):
                    if SESSIONS[key]['expires']<now: del SESSIONS[key]
                return SESSIONS.get(token)
        except (KeyError,ValueError): return None
    def admin(self):
        return self.session_info() is not None
    def rows(self,where,args=(),detailed=False):
        with sqlite3.connect(DB) as db:
            db.row_factory=sqlite3.Row
            fields='id,created_at,rating,meal,name,comment,status,publication_consent,consent_at,consent_version,hotel'
            if detailed: fields+=',food_rating,service_rating,wait_rating,ambience_rating,wait_not_applicable,submission_id'
            return [dict(r) for r in db.execute('SELECT '+fields+' FROM reviews WHERE '+where+' ORDER BY id DESC'+('' if detailed else ' LIMIT 200'),args)]
    def do_GET(self):
        parsed=urlparse(self.path)
        path=parsed.path
        selected_hotel=parse_qs(parsed.query).get('hotel',['all'])[0]
        pages={'/':'index.html','/index.html':'index.html','/avaliacoes':'reviews.html','/admin':'admin.html','/beach-hills':'index.html','/hotel-fenix':'index.html','/avaliacoes/beach-hills':'reviews.html','/avaliacoes/hotel-fenix':'reviews.html'}
        if path in pages: return self.respond(200,(ROOT/pages[path]).read_bytes(),'text/html; charset=utf-8')
        if path=='/assets/qrcode.js': return self.respond(200,(ROOT/'assets'/'qrcode.js').read_bytes(),'text/javascript; charset=utf-8')
        if path=='/api/reviews':
            hotel=selected_hotel if selected_hotel in ('beach_hills','hotel_fenix') else 'beach_hills'
            return self.respond(200,self.rows("status='approved' AND publication_consent=1 AND hotel=?",(hotel,)))
        if path=='/api/admin/session':
            session=self.session_info()
            return self.respond(200,{'authenticated':session is not None,'configured':bool(load_users()),'username':session['display_name'] if session else None})
        if path=='/api/admin/stats':
            if not self.admin(): return self.respond(401,{'error':'Entre no painel.'})
            with sqlite3.connect(DB) as db:
                stats={}
                where=' WHERE hotel=?' if selected_hotel in ('beach_hills','hotel_fenix') else ''
                args=(selected_hotel,) if where else ()
                for field in ('rating','food_rating','service_rating','wait_rating','ambience_rating'):
                    avg,count=db.execute('SELECT AVG('+field+'),COUNT('+field+') FROM reviews'+where,args).fetchone()
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
            if not 0<length<=24000: return self.respond(413,{})
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict): return self.respond(400,{})
            if self.path=='/api/reviews':
                batch='reviews' in data
                incoming=data.get('reviews') if batch else [data]
                if not isinstance(incoming,list) or not 1<=len(incoming)<=2: return self.respond(400,{'error':'Escolha almoço, jantar ou os dois.'})
                submission_id=secrets.token_urlsafe(16)
                prepared=[]
                seen=set()
                for item in incoming:
                    if not isinstance(item,dict): return self.respond(400,{})
                    rating,meal=item.get('rating'),item.get('meal')
                    name=data.get('name','') if batch else item.get('name','')
                    hotel=data.get('hotel','beach_hills') if batch else item.get('hotel','beach_hills')
                    comment=item.get('comment','')
                    if type(rating) is not int or rating not in range(1,6) or meal not in ('Almoço','Jantar') or hotel not in ('beach_hills','hotel_fenix') or meal in seen or not isinstance(name,str) or not isinstance(comment,str) or len(name)>80 or len(comment)>1500: return self.respond(400,{'error':'Confira a nota geral e os campos de cada refeição.'})
                    seen.add(meal)
                    categories=[item.get(k) for k in ('food_rating','service_rating','wait_rating','ambience_rating')]
                    if any(v is not None and (type(v) is not int or v not in range(1,6)) for v in categories): return self.respond(400,{'error':'As notas devem estar entre 1 e 5.'})
                    wait_na=item.get('wait_not_applicable',False)
                    if type(wait_na) is not bool or (wait_na and categories[2] is not None): return self.respond(400,{'error':'Confira a avaliação do tempo de espera.'})
                    consent=data.get('publication_consent',False) if batch else item.get('publication_consent',False)
                    if type(consent) is not bool: return self.respond(400,{})
                    token=secrets.token_urlsafe(32)
                    now=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    values=(rating,meal,name.strip().split(' ')[0],comment.strip(),hotel,hashlib.sha256(token.encode()).hexdigest(),int(consent),now if consent else None,('publication-v2' if batch else 'publication-v1') if consent else None,'pending' if consent else 'private',*categories,int(wait_na),submission_id)
                    prepared.append((values,token,meal))
                receipts=[]
                with sqlite3.connect(DB) as db:
                    for values,token,meal in prepared:
                        columns='rating,meal,name,comment,hotel,receipt,publication_consent,consent_at,consent_version,status,food_rating,service_rating,wait_rating,ambience_rating,wait_not_applicable,submission_id'
                        cursor=db.execute('INSERT INTO reviews ('+columns+') VALUES ('+','.join('?' for _ in values)+')',values)
                        receipts.append({'id':cursor.lastrowid,'receipt':token,'meal':meal})
                result={'ok':True,'receipts':receipts,'submission_id':submission_id}
                if not batch: result.update(receipts[0])
                return self.respond(201,result)
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
                users=load_users()
                if not users: return self.respond(503,{'error':'Usuários ainda não configurados. Execute python3 setup_users.py no terminal.'})
                username,password=data.get('username',''),data.get('password','')
                if not isinstance(username,str) or not isinstance(password,str) or len(username)>80 or len(password)>256: return self.respond(400,{})
                username=username.strip().casefold()
                auth=users.get(username)
                salt=auth['salt'] if auth else '00'*16
                computed=password_hash(password,salt)
                valid=auth is not None and hmac.compare_digest(computed,auth['hash'])
                if not valid: return self.respond(401,{'error':'Usuário ou senha incorretos.'})
                token=secrets.token_urlsafe(32)
                with LOCK:
                    SESSIONS[token]={'expires':time.time()+8*3600,'username':username,'display_name':auth.get('display_name',username)}
                    ATTEMPTS.pop(ip,None)
                secure='; Secure' if self.headers.get('X-Forwarded-Proto')=='https' else ''
                return self.respond(200,{'ok':True},cookie='beach_session='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800'+secure)
            if self.path.startswith('/api/admin/'):
                if not self.admin(): return self.respond(401,{'error':'Entre no painel.'})
                if self.path=='/api/admin/password':
                    session=self.session_info()
                    if not session: return self.respond(401,{'error':'Entre novamente no painel.'})
                    current,new,confirmation=data.get('current_password'),data.get('new_password'),data.get('confirmation')
                    if not all(isinstance(v,str) for v in (current,new,confirmation)) or len(current)>256 or not 8<=len(new)<=256 or new!=confirmation:
                        return self.respond(400,{'error':'A nova senha deve ter de 8 a 256 caracteres e a confirmação deve ser igual.'})
                    if current==new: return self.respond(400,{'error':'Escolha uma senha diferente da atual.'})
                    username=session['username']
                    attempt_key='password:'+username
                    with LOCK:
                        recent=[t for t in ATTEMPTS.get(attempt_key,[]) if t>time.time()-300]
                        if len(recent)>=5: return self.respond(429,{'error':'Muitas tentativas. Aguarde 5 minutos.'})
                        ATTEMPTS[attempt_key]=recent+[time.time()]
                        users=load_users()
                        account=users.get(username)
                        if not account or not hmac.compare_digest(password_hash(current,account['salt']),account['hash']):
                            return self.respond(403,{'error':'Senha atual incorreta.'})
                        salt=secrets.token_hex(16)
                        users[username]={**account,'salt':salt,'hash':password_hash(new,salt)}
                        save_users(users)
                        ATTEMPTS.pop(attempt_key,None)
                        for key in list(SESSIONS):
                            if SESSIONS[key]['username']==username: del SESSIONS[key]
                    return self.respond(200,{'ok':True},cookie='beach_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
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
