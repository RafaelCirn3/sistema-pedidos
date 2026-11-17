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

No painel /admin/, cadastre refeições e usuários. Os grupos **Cliente** e **Cozinha** são criados automaticamente pela migration. Atribua exatamente um grupo operacional a cada usuário; não marque usuários operacionais como staff ou superusuários. Administradores usam o Django Admin.

Clientes solicitam refeições disponíveis, acompanham pedidos próprios, cancelam pendências e avaliam entregas. A cozinha consulta todos os pedidos, prioriza pendentes em FIFO e confirma entregas ou cancelamentos. A fila se atualiza automaticamente a cada 30 segundos enquanto visível.

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
