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
- Crie Hotel e Devy com `python3 setup_users.py` no terminal. Defina a senha inicial no próprio terminal; a senha não aparece ao digitar e somente seu hash é armazenado. Não envie a senha pelo chat.
- A autorização de publicação é opcional e desmarcada. Sem ela, a avaliação é privada e o servidor bloqueia sua publicação. A autorização, data UTC e versão do texto ficam registradas. Avaliações anteriores à autorização permanecem privadas.
- O hóspede acompanha avaliações enviadas neste navegador usando um comprovante privado salvo localmente. Limpar os dados do navegador remove esse acompanhamento; o registro do hotel permanece. Não há prazo automático de aprovação.
- Sessão administrativa de 8 horas, encerrada ao reiniciar o servidor ou trocar a senha da respectiva conta. Cinco tentativas de login por IP a cada cinco minutos.
- Teste: `python3 test_moderation.py` usa banco temporário e não altera as avaliações reais.

## Notas por categoria
A experiência geral é obrigatória. Qualidade/sabor, atendimento, espera e limpeza/conforto são opcionais (1 a 5); espera aceita Não se aplica. O painel mostra notas individuais e médias de todos os registros, independentemente da publicação, excluindo campos vazios e não aplicáveis. O mural público mantém somente a nota geral e o comentário autorizado. Avaliações antigas não recebem notas presumidas. O CSV inclui todas as categorias.

## Preenchimento guiado
Formulário em três etapas: experiência e refeição; detalhes opcionais; comentário, nome e autorização. Os botões permitem voltar sem perder respostas. As notas detalhadas usam opções de toque de 1 a 5, com alternativas Não avaliar e Não se aplica para espera. Há progresso, resumo antes do envio e contador de caracteres. Nenhuma avaliação é enviada antes da etapa final.

O formulário recebe novas avaliações somente de almoço e jantar. Registros anteriores permanecem preservados.

## Almoço e jantar no mesmo envio
O hóspede escolhe Almoço, Jantar ou Os dois. A nota geral e os detalhes/comentários são independentes por refeição; nome e autorização são preenchidos uma vez. Ao avaliar os dois, há uma etapa de detalhes para cada refeição e um único botão final de envio. O servidor valida todo o conjunto antes de gravar as refeições na mesma transação, vinculadas por submission_id. O mural e a moderação continuam mostrando cada refeição separadamente.

## Área da equipe
Painel com resumo dos 200 registros mais recentes, médias gerais, abas por situação, busca por nome/comentário e filtro por refeição. As notas por categoria ficam recolhidas em cada avaliação. Opiniões privadas não apresentam ações de publicação. O login e as permissões continuam obrigatórios.

## Usuários e troca de senha
- Hotel: equipe do hotel. Devy: desenvolvimento do site. Ambos têm acesso total. O login aceita maiúsculas e minúsculas.
- Execute `python3 setup_users.py` para criar apenas as contas ausentes, preservando contas existentes. Informe a senha inicial solicitada pelo responsável. Senhas e usuários ficam em data/users.json, fora do Git, com hashes scrypt e arquivo restrito.
- No painel, Alterar senha pede a senha atual, a nova e sua confirmação. A nova senha deve ter no mínimo 8 caracteres. A troca encerra todas as sessões daquela conta, sem afetar o outro usuário.
- Contas anteriores em data/admin.json continuam compatíveis e são preservadas ao cadastrar os novos acessos.
- Testes isolados: `python3 -m unittest test_moderation test_users`.
