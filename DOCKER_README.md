# Docker Setup - AXM ClubPro

Configuração Docker unificada para desenvolvimento e produção usando variáveis de ambiente.

## Configuração Inicial

1. **Copie o arquivo de exemplo:**
   ```bash
   cp .env.example .env
   ```

2. **Edite o `.env`** com suas configurações

## Uso

### Desenvolvimento (com hot-reload)

```bash
# Iniciar apenas Django e banco (sem Nginx)
docker-compose up -d db web

# Acessar em http://localhost:8000
```

### Produção (com Nginx)

```bash
# Iniciar todos os serviços incluindo Nginx
docker-compose --profile nginx up -d

# Acessar em http://localhost (porta 80)
```

## Variáveis de Ambiente Importantes

### Obrigatórias no `.env`:
- `DB_NAME` - Nome do banco de dados
- `DB_USER` - Usuário do banco
- `DB_PASSWORD` - Senha do banco
- `SECRET_KEY` - Secret key do Django
- `ALLOWED_HOSTS` - Hosts permitidos (separados por vírgula)
- `DEBUG` - True para desenvolvimento, False para produção

### Opcionais:
- `USE_SSL` - True para habilitar SSL (quando configurado)
- `WEB_COMMAND` - Comando para iniciar o servidor (padrão: runserver)
- `WEB_PORT` - Porta do Django (padrão: 8000)
- `NGINX_PORT` - Porta do Nginx (padrão: 80)
- `DB_PORT` - Porta do PostgreSQL no host (padrão: 5436)

## Comandos Úteis

```bash
# Ver logs
docker-compose logs -f web

# Criar superusuário
docker-compose exec web python manage.py createsuperuser

# Executar migrações
docker-compose exec web python manage.py migrate

# Coletar arquivos estáticos
docker-compose exec web python manage.py collectstatic

# Acessar shell Django
docker-compose exec web python manage.py shell

# Parar serviços
docker-compose down

# Reconstruir após mudanças
docker-compose build --no-cache
docker-compose up -d
```

## Produção com Gunicorn

Para produção, configure no `.env`:

```env
WEB_COMMAND=gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 clubpro.wsgi:application
DEBUG=False
USE_SSL=False  # Mude para True quando configurar SSL
```

## Estrutura

- **docker-compose.yml** - Configuração unificada
- **Dockerfile** - Imagem Docker unificada
- **nginx.conf** - Configuração do Nginx (opcional, use `--profile nginx`)
- **wait-for-db.py** - Script para aguardar PostgreSQL
- **.env** - Variáveis de ambiente (não commitado)
