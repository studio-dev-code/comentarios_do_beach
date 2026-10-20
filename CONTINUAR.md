# Continuidade — Restaurante Beach Hills
Atualizado em 18/10/2026, horário de Brasília.

## Projeto
Repositório: https://github.com/studio-dev-code/comentarios_do_beach
Pasta no Codespaces: /workspaces/comentarios_do_beach

## Concluído
- Formulário responsivo com etapas curtas e progresso.
- Escolha Almoço, Jantar ou Os dois. As duas refeições têm notas e comentários independentes, enviados de uma vez. Café da manhã removido das novas avaliações.
- Nota geral obrigatória; qualidade/sabor, atendimento, espera e limpeza/conforto opcionais. Espera aceita Não se aplica.
- Autorização de publicação opcional e desmarcada. Sem autorização, avaliação privada e publicação bloqueada no servidor.
- Mural público em /avaliacoes; após enviar, o hóspede acompanha a própria avaliação neste navegador por comprovantes locais, mesmo antes da aprovação.
- Painel em /admin com resumo, médias, filtros por situação/refeição, busca, detalhes recolhíveis e moderação.
- Implementado suporte a Hotel (equipe) e Devy (desenvolvimento), ambos com acesso total, identificação da conta e alteração da própria senha.
- Troca de senha confirma a senha atual e encerra as sessões da respectiva conta; não afeta a outra.
- Código e documentação enviados à branch main do GitHub.

## Onde paramos
As contas Hotel e Devy ainda NÃO foram ativadas. A confirmação foi feita sem ler ou mostrar hashes/senhas. O terminal 14 foi deixado em setup_users.py aguardando a senha inicial, mas pode não permanecer aberto entre sessões. Não presumir que a criação terminou.

## Retomar
1. Abra este Codespace e leia README.md e CONTINUAR.md.
2. Se necessário, execute python3 server.py para iniciar a porta 8000.
3. Para ativar os usuários, execute python3 setup_users.py. O responsável digita a senha inicial e confirma no terminal; não registrar senhas no Git. O script cria apenas contas ausentes e preserva existentes. A entrada de credenciais fica a cargo do usuário.
4. Entre em /admin; cada usuário encontra Alterar senha no topo. Novas senhas têm mínimo de 8 caracteres.
5. Próximo passo: escolher/configurar hospedagem permanente com HTTPS e armazenamento persistente; depois gerar QR Code para o endereço definitivo. A prévia do Codespaces depende do ambiente ligado e tem acesso privado. GitHub Pages não executa o servidor Python.

## Dados e validação
- Banco: data/reviews.sqlite3. Contas: data/users.json (quando ativadas); compatibilidade com data/admin.json. A pasta data é ignorada pelo Git e permanece somente neste Codespace. Não enviá-la ao repositório.
- Backup local do banco feito em data/backups ao encerrar esta sessão. Backups também não vão para o GitHub.
- Exportação: python3 export_reviews.py > avaliacoes.csv
- Testes isolados aprovados: python3 -m unittest test_moderation test_users. Cobrem moderação, autorização, médias, envio conjunto sem gravação parcial e independência das contas/senhas.
- Visual e interações conferidos no navegador; prévias administrativas usaram dados fictícios em servidor temporário separado, já encerrado.

## Correção em 20/10/2026
- Duas avaliações reais encontradas no banco, ambas privadas; backup SQLite realizado em data/backups antes das alterações.
- Painel agora inicia em Todas e atualiza automaticamente a cada 15 segundos e ao voltar à aba.
- Consulta administrativa sem limite de 200; mural público mantém limite.
- Testes test_moderation e test_users aprovados, incluindo avaliação privada no painel. Teste isolado com 205 registros e sintaxe JavaScript aprovados.
- Contas ainda ausentes: responsável precisa executar setup_users.py e digitar a senha. Não afirmar que ativação terminou.
- Hospedagem permanente e backup externo continuam pendentes; Codespaces precisa permanecer ligado.
