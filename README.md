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
Os registros ficam em `data/reviews.sqlite3`, fora do Git e sem rota pública de leitura. Faça backup dessa pasta. Os comentários não são publicados automaticamente.

## Hospedar para os hóspedes
Use hospedagem Python com volume persistente para `data/`, HTTPS e variável PORT opcional. GitHub Pages não executa este servidor. Codespaces serve para desenvolvimento e para quando suspenso. Após publicar, use o endereço definitivo no QR Code. Antes de uso público em escala, adicione proteção contra spam e uma política de retenção dos comentários.
