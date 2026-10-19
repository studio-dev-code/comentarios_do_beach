import getpass, secrets
from server import ROOT,load_users,save_users,password_hash
users=load_users()
missing=[(key,title) for key,title in [('hotel','Hotel'),('devy','Devy')] if key not in users]
if not missing: raise SystemExit('Hotel e Devy já estão cadastrados. Nenhuma senha foi alterada.')
print('Criar acessos com permissão total: '+', '.join(title for _,title in missing))
password=getpass.getpass('Senha inicial para os novos usuários: ')
confirmation=getpass.getpass('Repita a senha inicial: ')
if not password or len(password)>256 or password!=confirmation: raise SystemExit('As senhas não conferem. Nenhum usuário foi criado.')
for key,title in missing:
    salt=secrets.token_hex(16)
    users[key]={'display_name':title,'salt':salt,'hash':password_hash(password,salt)}
save_users(users)
print('Usuários criados com acesso total. Cada um pode alterar sua própria senha no painel.')
