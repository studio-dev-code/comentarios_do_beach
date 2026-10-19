import csv, sqlite3, sys
from server import DB
with sqlite3.connect(DB) as db:
    writer=csv.writer(sys.stdout)
    writer.writerow(['ID','Data UTC','Nota','Refeição','Nome','Comentário'])
    for row in db.execute('SELECT * FROM reviews ORDER BY id DESC'):
        writer.writerow([(chr(39)+v if isinstance(v,str) and v.startswith(('=','+','-','@',chr(9),chr(13))) else v) for v in row])
