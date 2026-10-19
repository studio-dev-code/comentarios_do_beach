import csv, sqlite3, sys
from server import DB
with sqlite3.connect(DB) as db:
    writer=csv.writer(sys.stdout)
    writer.writerow(['ID','Data UTC','Nota','Refeição','Nome','Comentário','Status','Autorização de publicação','Autorizado em UTC','Versão do texto'])
    for row in db.execute('SELECT id,created_at,rating,meal,name,comment,status,publication_consent,consent_at,consent_version FROM reviews ORDER BY id DESC'):
        writer.writerow([(chr(39)+v if isinstance(v,str) and v.startswith(('=','+','-','@',chr(9),chr(13))) else v) for v in row])
