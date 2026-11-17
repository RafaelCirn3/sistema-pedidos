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

A aba **Histórico de pedidos** (/pedidos/historico/) reúne entregues e cancelados, com filtros de avaliações. O cliente pode avaliar entregas próprias por essa aba; a cozinha consulta o histórico de todos os clientes. A tela inicial apresenta exclusivamente pedidos pendentes.

## Desenvolvimento sem Docker

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
