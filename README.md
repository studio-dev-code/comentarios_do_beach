# Restaurante Beach Hills
Página de avaliação responsiva, sem login para hóspedes. Python 3 e SQLite, sem dependências externas.

## Executar
```bash
python3 server.py
```
No Codespaces, abra a porta 8000 na aba Portas. O endereço de prévia exige acesso ao Codespace enquanto a porta for privada.

## Consultar avaliações
No terminal do hotel:
```bash
python3 export_reviews.py > avaliacoes.csv
```
Os registros ficam em `data/reviews.sqlite3`, fora do Git e sem rota pública de leitura. Faça backup dessa pasta. Somente avaliações autorizadas pelo hóspede e aprovadas pela equipe são publicadas.

## Hospedar para os hóspedes
Use hospedagem Python com volume persistente para `data/`, HTTPS e variável PORT opcional. GitHub Pages não executa este servidor. Codespaces serve para desenvolvimento e para quando suspenso. Após publicar, use o endereço definitivo no QR Code. Antes de uso público em escala, adicione proteção contra spam e uma política de retenção dos comentários.

## Mural e moderação
- `/avaliacoes`: mural público, com até 200 avaliações aprovadas mais recentes.
- `/admin`: painel protegido; aprovar, não publicar ou voltar para análise.
- Crie o administrador com `python3 setup_admin.py` no terminal. Defina usuário e senha (mínimo 12 caracteres); a senha não aparece ao digitar e somente seu hash é armazenado. Não envie a senha pelo chat.
- A autorização de publicação é opcional e desmarcada. Sem ela, a avaliação é privada e o servidor bloqueia sua publicação. A autorização, data UTC e versão do texto ficam registradas. Avaliações anteriores à autorização permanecem privadas.
- O hóspede acompanha avaliações enviadas neste navegador usando um comprovante privado salvo localmente. Limpar os dados do navegador remove esse acompanhamento; o registro do hotel permanece. Não há prazo automático de aprovação.
- Sessão administrativa de 8 horas, encerrada ao reiniciar o servidor. Cinco tentativas de login por IP a cada cinco minutos.
- Teste: `python3 test_moderation.py` usa banco temporário e não altera as avaliações reais.
