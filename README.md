# Mesa — Sistema de pedidos

MVP Django MVT para pedidos de refeições, com templates responsivos, autenticação por sessão, PostgreSQL no Docker e Django Admin.

## Executar com Docker

1. Copie `.env.example` para `.env` e preencha a senha do banco e uma chave secreta forte.
2. Execute:

```bash
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
```

Acesse http://localhost:8000. As migrations e arquivos estáticos são preparados na inicialização.

## Configuração inicial

No painel /admin/, cadastre usuários da cozinha e atribua o grupo **Cozinha**. Os grupos **Cliente** e **Cozinha** são criados automaticamente pela migration. Clientes podem criar sua conta em /cadastro/ com nome, e-mail, WhatsApp e senha; o e-mail é usado para login. Não marque usuários operacionais como staff ou superusuários. Administradores usam o Django Admin.

A cozinha gerencia o cardápio em /cardapio/, incluindo fotos JPG/PNG/WebP de até 5 MB, disponibilidade e opções de seleção (checkboxes). As escolhas marcadas ficam registradas no pedido, mesmo se a opção for renomeada ou excluída. O volume Docker media preserva as imagens entre recriações do contêiner; inclua-o no backup.

Clientes solicitam refeições disponíveis, acompanham pedidos próprios e cancelam pendências. A cozinha consulta os pedidos pendentes de todos os clientes em FIFO e confirma entregas ou cancelamentos. A fila se atualiza automaticamente a cada 30 segundos enquanto visível.

A aba **Histórico de pedidos** (/pedidos/historico/) reúne entregues e cancelados, com filtros de avaliações. O cliente pode avaliar entregas próprias por essa aba; a cozinha consulta o histórico de todos os clientes. A tela inicial da cozinha apresenta somente pedidos pendentes; a do cliente apresenta também entregas ainda não avaliadas, com botão para avaliar.

### Exclusões administrativas

O Django Admin permite exclusões individuais ou em lote de pedidos, avaliações, registros de histórico, pratos, opções e perfis, conforme as permissões de exclusão do Django. A confirmação nativa do Admin lista os objetos relacionados que também serão excluídos.

- Excluir um cliente remove seu perfil e seus pedidos, incluindo avaliações e histórico desses pedidos.
- Excluir um prato remove suas opções, pedidos, avaliações e histórico dos respectivos pedidos.
- Excluir um pedido remove suas avaliações e histórico.
- Excluir um usuário que apenas atuou como responsável por uma alteração mantém os históricos de outros pedidos, com o campo responsável vazio.
- Excluir uma opção não altera as escolhas já registradas nos pedidos.

As cascatas são executadas pelo ORM do Django. Exclusões são definitivas; utilize a desativação de pratos/usuários para preservar dados históricos quando necessário e mantenha backups.

## Desenvolvimento sem Docker

### Dados de demonstração (seed)

Após as migrations, execute apenas em ambiente de teste:

```bash
docker compose exec web python manage.py seed
# Ou, sem Docker:
python manage.py seed
```

O comando cria três contas de demonstração: `demo-admin` (administrador), `demo-cozinha` (cozinha) e `cliente.demo@example.test` (cliente). As senhas iniciais são aleatórias, exibidas uma única vez no terminal. Guarde-as em local seguro e não utilize essas contas em produção. O comando não redefine senhas nem promove usuários existentes.

Cadastra cinco pratos, checkboxes de personalização e copia fotos ilustrativas do Wikimedia Commons, já incluídas no repositório, para o volume de mídia. Funciona offline com as fotos distribuídas; se algum arquivo estiver ausente, tenta obtê-lo da fonte original. Executar novamente não duplica pratos com o mesmo nome nem usuários. Use `--sem-imagens` para popular somente os dados.

Créditos das fotografias (redimensionadas para o cardápio):

| Prato | Fonte / autor | Licença |
|---|---|---|
| Feijoada completa | [Brazilian food Feijoada.jpg](https://commons.wikimedia.org/wiki/File:Brazilian_food_Feijoada.jpg) — Wilfredor | CC0 1.0 |
| Peixe grelhado | [Arroz, feijão e peixe grelhado.jpg](https://commons.wikimedia.org/wiki/File:Arroz,_feij%C3%A3o_e_peixe_grelhado.jpg) — Maryleine | CC0 1.0 |
| Macarrão à bolonhesa | [Pastabolognese.jpg](https://commons.wikimedia.org/wiki/File:Pastabolognese.jpg) — Ludraman | Domínio público |
| Omelete da casa | [Eggs omelette.jpg](https://commons.wikimedia.org/wiki/File:Eggs_omelette.jpg) — National Cancer Institute | Domínio público |
| Salada fresca | [Salad On Plate.jpg](https://commons.wikimedia.org/wiki/File:Salad_On_Plate.jpg) — KittensMittens4 | CC0 1.0 |

### Instalação local

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
python manage.py test
```

Sem DB_HOST, usa SQLite para desenvolvimento local. Com Docker, PostgreSQL 16 é obrigatório.

## Produção

Configure Nginx no host com HTTPS, proxy para 127.0.0.1:8000, cabeçalho X-Forwarded-Proto e host correto. Defina DJANGO_DEBUG=False, DJANGO_SECURE_COOKIES=True, DJANGO_ALLOWED_HOSTS e DJANGO_CSRF_TRUSTED_ORIGINS. WhiteNoise entrega arquivos estáticos coletados. Mantenha o banco privado e faça backups periódicos de pgdata com pg_dump. Não use down -v se precisar preservar os dados.
