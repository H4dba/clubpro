# Docker Setup para AXM ClubPro

Este projeto está configurado para rodar com Docker Compose, facilitando o desenvolvimento e deploy.

## Pré-requisitos

- Docker Desktop (Windows/Mac) ou Docker Engine (Linux)
- Docker Compose v3.8 ou superior

## Configuração Inicial

1. **Crie um arquivo `.env`** baseado no `.env.example`:

```bash
cp .env.example .env
```

2. **Configure as variáveis de ambiente** no arquivo `.env`:

```env
# Database Configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=clubpro_db
DB_USER=clubpro_user
DB_PASSWORD=clubpro_password
DB_HOST=db
DB_PORT=5432

# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Lichess Configuration
HOST=localhost
```

## Comandos Docker

### Iniciar os serviços

```bash
docker-compose up -d
```

Isso irá:
- Criar e iniciar o banco de dados PostgreSQL
- Construir a imagem do Django
- Executar migrações automaticamente
- Coletar arquivos estáticos
- Iniciar o servidor Django na porta 8000

### Ver logs

```bash
# Todos os serviços
docker-compose logs -f

# Apenas Django
docker-compose logs -f web

# Apenas banco de dados
docker-compose logs -f db
```

### Parar os serviços

```bash
docker-compose down
```

### Parar e remover volumes (limpar dados)

```bash
docker-compose down -v
```

### Reconstruir após mudanças

```bash
# Reconstruir apenas o serviço web
docker-compose up -d --build web

# Reconstruir tudo
docker-compose up -d --build
```

### Executar comandos Django

```bash
# Criar superusuário
docker-compose exec web python manage.py createsuperuser

# Executar migrações manualmente
docker-compose exec web python manage.py migrate

# Coletar arquivos estáticos
docker-compose exec web python manage.py collectstatic

# Abrir shell Django
docker-compose exec web python manage.py shell

# Executar testes
docker-compose exec web python manage.py test
```

### Acessar o banco de dados

```bash
# Via psql dentro do container
docker-compose exec db psql -U clubpro_user -d clubpro_db

# Ou usar uma ferramenta externa conectando em:
# Host: localhost
# Port: 5436
# Database: clubpro_db
# User: clubpro_user
# Password: clubpro_password
```

## Estrutura dos Serviços

- **web**: Serviço Django rodando na porta 8000
- **db**: PostgreSQL 15 rodando na porta 5436 (host) / 5432 (container)

## Volumes

- `postgres_data`: Dados persistentes do PostgreSQL
- `static_volume`: Arquivos estáticos coletados
- `media_volume`: Arquivos de mídia enviados pelos usuários

## Troubleshooting

### Erro de conexão com banco de dados

Certifique-se de que o serviço `db` está rodando e saudável:

```bash
docker-compose ps
```

### Reexecutar migrações

```bash
docker-compose exec web python manage.py migrate
```

### Limpar cache e reconstruir

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Verificar logs de erro

```bash
docker-compose logs web | grep -i error
```

## Desenvolvimento

Para desenvolvimento, os arquivos são montados como volumes, então mudanças no código são refletidas automaticamente. Você pode precisar reiniciar o serviço web:

```bash
docker-compose restart web
```

## Produção

Para produção, você deve:

1. Alterar `DEBUG=False` no `.env`
2. Configurar `SECRET_KEY` seguro
3. Configurar `ALLOWED_HOSTS` adequadamente
4. Usar um servidor WSGI como Gunicorn ao invés do runserver
5. Configurar um servidor web reverso (nginx) para servir arquivos estáticos
