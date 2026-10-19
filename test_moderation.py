import json, sqlite3, tempfile, threading, unittest, urllib.request, urllib.error, http.cookiejar, secrets
from pathlib import Path
from http.cookiejar import CookieJar
import server
class ModerationTest(unittest.TestCase):
    def test_flow(self):
        old_root,old_db=server.ROOT,server.DB
        with tempfile.TemporaryDirectory() as folder:
            server.ROOT=Path(folder); (server.ROOT/'data').mkdir()
            server.DB=server.ROOT/'data'/'reviews.sqlite3'
            with sqlite3.connect(old_db) as source, sqlite3.connect(server.DB) as target: source.backup(target)
            with sqlite3.connect(server.DB) as db: db.execute('DELETE FROM reviews')
            salt=secrets.token_hex(16)
            (server.ROOT/'data'/'admin.json').write_text(json.dumps(dict(username='test-admin',salt=salt,hash=server.password_hash('test-only-password',salt))))
            http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
            threading.Thread(target=http.serve_forever,daemon=True).start()
            base='http://127.0.0.1:'+str(http.server_port)
            guest=urllib.request.build_opener(); admin=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
            def call(client,path,data=None):
                req=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers={'X-Requested-With':'BeachHills','Content-Type':'application/json'})
                with client.open(req) as response: return json.load(response)
            try:
                receipt=call(guest,'/api/reviews',dict(rating=1,meal='Jantar',name='Maria Silva',comment='<script>alert(1)</script>',publication_consent=True,food_rating=2,service_rating=4,wait_rating=None,wait_not_applicable=True,ambience_rating=5))
                self.assertEqual(call(guest,'/api/reviews'),[])
                own=call(guest,'/api/reviews/own',{'receipt':receipt['receipt']})
                self.assertEqual(own[0]['status'],'pending');self.assertEqual(own[0]['name'],'Maria')
                self.assertEqual(call(guest,'/api/reviews/own',{'receipt':'wrong'}),[])
                with self.assertRaises(urllib.error.HTTPError) as error: call(guest,'/api/admin/moderate',dict(id=receipt['id'],status='approved'))
                self.assertEqual(error.exception.code,401);error.exception.close()
                call(admin,'/api/admin/login',dict(username='test-admin',password='test-only-password'))
                details=call(admin,'/api/admin/reviews')[0]
                self.assertEqual(details['food_rating'],2)
                self.assertEqual(details['wait_not_applicable'],1)
                self.assertNotIn('food_rating',own[0])
                stats=call(admin,'/api/admin/stats')
                self.assertEqual(stats['food_rating'],{'average':2.0,'count':1})
                self.assertEqual(stats['wait_rating'],{'average':None,'count':0})
                for value in (0,6,True,'5'):
                    with self.assertRaises(urllib.error.HTTPError) as error: call(guest,'/api/reviews',dict(rating=5,meal='Jantar',food_rating=value))
                    self.assertEqual(error.exception.code,400);error.exception.close()
                call(admin,'/api/admin/moderate',dict(id=receipt['id'],status='approved'))
                self.assertEqual(call(guest,'/api/reviews')[0]['rating'],1)
                self.assertNotIn('food_rating',call(guest,'/api/reviews')[0])
                self.assertNotIn('receipt',call(guest,'/api/reviews')[0])
                call(admin,'/api/admin/moderate',dict(id=receipt['id'],status='rejected'))
                self.assertEqual(call(guest,'/api/reviews'),[])
                private=call(guest,'/api/reviews',dict(rating=5,meal='Almoço',comment='Privada'))
                self.assertEqual(call(guest,'/api/reviews/own',{'receipt':private['receipt']})[0]['status'],'private')
                with self.assertRaises(urllib.error.HTTPError) as error: call(admin,'/api/admin/moderate',dict(id=private['id'],status='approved'))
                self.assertEqual(error.exception.code,409);error.exception.close()
                stats=call(admin,'/api/admin/stats')
                self.assertEqual(stats['food_rating']['count'],1)
                self.assertEqual(stats['rating'],{'average':3.0,'count':2})
                self.assertEqual(call(guest,'/api/reviews'),[])
                two=call(guest,'/api/reviews',dict(name='Ana Silva',publication_consent=True,reviews=[dict(meal='Almoço',rating=5,food_rating=4,comment='Almoço ótimo'),dict(meal='Jantar',rating=2,service_rating=3,comment='Jantar demorado')]))
                self.assertEqual(len(two['receipts']),2)
                lunch=call(guest,'/api/reviews/own',dict(receipt=two['receipts'][0]['receipt']))[0]
                dinner=call(guest,'/api/reviews/own',dict(receipt=two['receipts'][1]['receipt']))[0]
                self.assertEqual((lunch['meal'],lunch['rating'],dinner['meal'],dinner['rating']),('Almoço',5,'Jantar',2))
                self.assertEqual(lunch['status'],'pending');self.assertEqual(dinner['status'],'pending')
                details=call(admin,'/api/admin/reviews')
                pair=[r for r in details if r['submission_id']==two['submission_id']]
                self.assertEqual(len(pair),2)
                self.assertEqual(call(guest,'/api/reviews'),[])
                before=len(details)
                for invalid in ([dict(meal='Almoço',rating=5),dict(meal='Jantar',rating=7)],[dict(meal='Almoço',rating=5),dict(meal='Almoço',rating=4)]):
                    with self.assertRaises(urllib.error.HTTPError) as error: call(guest,'/api/reviews',dict(reviews=invalid))
                    self.assertEqual(error.exception.code,400);error.exception.close()
                    self.assertEqual(len(call(admin,'/api/admin/reviews')),before)
                one=call(guest,'/api/reviews',dict(reviews=[dict(meal='Jantar',rating=4)],publication_consent=False))
                self.assertEqual(len(one['receipts']),1)
                self.assertEqual(call(guest,'/api/reviews/own',dict(receipt=one['receipts'][0]['receipt']))[0]['status'],'private')
                call(admin,'/api/admin/logout',{})
                self.assertFalse(call(admin,'/api/admin/session')['authenticated'])
            finally:
                http.shutdown();http.server_close();server.ROOT,server.DB=old_root,old_db
if __name__=='__main__': unittest.main()
