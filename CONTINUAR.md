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

## Dois hotéis — 20/10/2026
- Implementados /beach-hills e /hotel-fenix. Cada formulário identifica automaticamente o hotel ao enviar almoço, jantar ou ambos.
- Murais /avaliacoes/beach-hills e /avaliacoes/hotel-fenix isolados por hotel; avaliações próprias também filtradas. / e /avaliacoes mantêm compatibilidade com Beach Hills.
- Dois registros reais existentes preservados, migrados para beach_hills; backup antes da alteração em data/backups.
- Painel /admin unificado com filtro Os dois hotéis / Beach Hills / Hotel Fênix; identificação nos registros, contagens e médias por hotel.
- Identidades inspiradas nos sites oficiais, fotos oficiais de referência, botão visível para o site do hotel no cabeçalho e na apresentação. Layout responsivo para celular.
- Exportação CSV inclui Hotel. Contas existentes e senhas preservadas.
- Testes de integração e sintaxe JavaScript aprovados. Prévia externa bloqueada pelo navegador (ERR_BLOCKED_BY_CLIENT), conferência visual pendente.
- Servidor iniciado na porta 8000. Hospedagem definitiva e QR Codes impressos devem usar endereço público permanente; este Codespaces precisa estar ativo e a prévia segue com o acesso anterior.

## Links e QR Codes no ADM — 20/10/2026
- Seção Links e QR Codes dos hotéis no início do painel autenticado, com cartão Beach Hills e cartão Hotel Fênix.
- Link calculado pelo endereço atual do sistema e rota específica do hotel; botões Copiar link, Abrir avaliação, Baixar QR PNG e Baixar QR SVG.
- QR gerado localmente pela biblioteca qrcode-generator 1.4.4, incluída em assets/qrcode.js com a licença original preservada. Nenhum serviço externo recebe o link.
- PNG de alta resolução com módulos inteiros e margem branca de quatro módulos; SVG vetorial disponível para impressão.
- Aviso no ADM quando o endereço for prévia do Codespaces. Ao hospedar em endereço permanente, links e QR Codes passam a usar esse domínio automaticamente.
- Sintaxe, geração distinta dos dois QR Codes, margem e endpoint da biblioteca verificados; testes de integração existentes aprovados. Servidor reiniciado na porta 8000.
