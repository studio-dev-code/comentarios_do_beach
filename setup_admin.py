import getpass, json, secrets, os
from server import ROOT,password_hash
p=ROOT/'data'/'admin.json'
if (ROOT/'data'/'users.json').exists(): raise SystemExit('Use o painel para alterar sua senha; Hotel e Devy já estão configurados.')
if p.exists(): raise SystemExit('Administrador já configurado. Nenhuma alteração realizada.')
username=input('Usuário do administrador: ').strip()
password=getpass.getpass('Senha (mínimo 12 caracteres): ')
confirmation=getpass.getpass('Repita a senha: ')
if not username or len(password)<12 or len(password)>256 or password!=confirmation: raise SystemExit('Confira o usuário e a senha. Nada foi salvo.')
salt=secrets.token_hex(16)
fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as file: json.dump(dict(username=username,salt=salt,hash=password_hash(password,salt)),file)
print('Administrador criado. Abra /admin para entrar.')
