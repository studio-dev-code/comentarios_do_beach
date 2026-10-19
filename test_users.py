import json,secrets,sqlite3,tempfile,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from http.cookiejar import CookieJar
import server
class UsersTest(unittest.TestCase):
    def test_accounts(self):
        root,database=server.ROOT,server.DB
        with tempfile.TemporaryDirectory() as folder:
            server.ROOT=Path(folder);(server.ROOT/'data').mkdir();server.DB=server.ROOT/'data'/'reviews.sqlite3'
            with sqlite3.connect(database) as source,sqlite3.connect(server.DB) as target:source.backup(target)
            with sqlite3.connect(server.DB) as db:db.execute('DELETE FROM reviews')
            users={}
            for name in ('hotel','devy'):
                salt=secrets.token_hex(16);users[name]=dict(display_name=name.title(),salt=salt,hash=server.password_hash('initial-test-password',salt))
            server.save_users(users)
            http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);threading.Thread(target=http.serve_forever,daemon=True).start()
            base='http://127.0.0.1:'+str(http.server_port)
            def client():return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
            def call(browser,path,data=None):
                request=urllib.request.Request(base+path,data=None if data is None else json.dumps(data).encode(),headers={'X-Requested-With':'BeachHills','Content-Type':'application/json'})
                with browser.open(request) as response:return json.load(response)
            def rejected(browser,path,data,code):
                with self.assertRaises(urllib.error.HTTPError) as error:call(browser,path,data)
                self.assertEqual(error.exception.code,code);error.exception.close()
            hotel,hotel2,devy,guest=client(),client(),client(),client()
            try:
                for browser,name in [(hotel,'Hotel'),(hotel2,'HOTEL'),(devy,'Devy')]:
                    call(browser,'/api/admin/login',dict(username=name,password='initial-test-password'))
                    self.assertTrue(call(browser,'/api/admin/session')['authenticated'])
                    self.assertIsInstance(call(browser,'/api/admin/reviews'),list)
                    self.assertIn('rating',call(browser,'/api/admin/stats'))
                review=call(guest,'/api/reviews',dict(rating=4,meal='Almoço',publication_consent=True))
                call(hotel,'/api/admin/moderate',dict(id=review['id'],status='approved'))
                call(devy,'/api/admin/moderate',dict(id=review['id'],status='pending'))
                rejected(guest,'/api/admin/password',dict(current_password='x',new_password='new-test-password',confirmation='new-test-password'),401)
                rejected(hotel,'/api/admin/password',dict(current_password='wrong',new_password='new-test-password',confirmation='new-test-password'),403)
                rejected(hotel,'/api/admin/password',dict(current_password='initial-test-password',new_password='new-test-password',confirmation='different-password'),400)
                call(hotel,'/api/admin/password',dict(current_password='initial-test-password',new_password='new-test-password',confirmation='new-test-password'))
                self.assertFalse(call(hotel,'/api/admin/session')['authenticated']);self.assertFalse(call(hotel2,'/api/admin/session')['authenticated'])
                self.assertTrue(call(devy,'/api/admin/session')['authenticated'])
                rejected(hotel,'/api/admin/login',dict(username='hotel',password='initial-test-password'),401)
                call(hotel,'/api/admin/login',dict(username='hotel',password='new-test-password'))
                self.assertEqual(call(hotel,'/api/admin/session')['username'],'Hotel')
                self.assertNotIn('new-test-password',json.dumps(server.load_users()))
                self.assertEqual(server.load_users()['devy']['hash'],users['devy']['hash'])
            finally:http.shutdown();http.server_close();server.ROOT,server.DB=root,database
if __name__=='__main__':unittest.main()
