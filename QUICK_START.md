# Quick Start - Deploy em Produção

## Configuração Rápida

### 1. Configure o arquivo `.env`

```bash
cp .env.example .env
nano .env
```

Configure estas variáveis:

```env
# Database
DB_NAME=clubpro_db
DB_USER=clubpro_user
DB_PASSWORD=SUA_SENHA_FORTE_AQUI

# Django - IMPORTANTE para produção
DEBUG=False
SECRET_KEY=GERE_UMA_SECRET_KEY_FORTE_AQUI
ALLOWED_HOSTS=seu-ip-publico,seu-dominio.com,localhost,127.0.0.1
HOST=seu-dominio.com  # ou seu IP público

# Para usar Gunicorn em produção (descomente):
WEB_COMMAND=gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 clubpro.wsgi:application

# Opcional: remover exposição da porta 8000 em produção
# Comente ou remova WEB_PORT=8000 para esconder Django
```

### 2. Gerar SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Configurar Firewall (Ubuntu/Debian)

```bash
# Permitir porta 80 (HTTP)
sudo ufw allow 80/tcp

# Permitir porta 443 se usar SSL depois
sudo ufw allow 443/tcp

# Verificar status
sudo ufw status
```

### 4. Iniciar Serviços

```bash
# Parar serviços existentes
docker-compose down

# Reconstruir e iniciar
docker-compose build
docker-compose up -d

# Verificar logs
docker-compose logs -f
```

### 5. Verificar

```bash
# De dentro da VM
curl http://localhost

# De outra máquina (use o IP público da VM)
curl http://SEU_IP_PUBLICO
```

## Troubleshooting

### Não consegue acessar de fora da VM

1. **Verificar firewall:**
   ```bash
   sudo ufw status
   sudo ufw allow 80/tcp
   ```

2. **Verificar se Nginx está rodando:**
   ```bash
   docker-compose ps
   docker-compose logs nginx
   ```

3. **Verificar ALLOWED_HOSTS no .env:**
   - Deve incluir o IP público da VM
   - Exemplo: `ALLOWED_HOSTS=123.45.67.89,localhost,127.0.0.1`

4. **Verificar se está usando Gunicorn:**
   ```bash
   docker-compose logs web | grep -i gunicorn
   ```

5. **Verificar configuração de rede da VM:**
   - No Google Cloud/AWS/Azure, verifique Security Groups/Firewall Rules
   - Deve permitir tráfego HTTP (porta 80) de qualquer origem (0.0.0.0/0)

### Está rodando runserver ao invés de Gunicorn

Certifique-se de que no `.env` você tem:
```env
WEB_COMMAND=gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 clubpro.wsgi:application
```

Depois reinicie:
```bash
docker-compose down
docker-compose up -d
```

### Nginx não está iniciando

```bash
# Ver logs do Nginx
docker-compose logs nginx

# Verificar se nginx.conf está correto
docker-compose exec nginx nginx -t
```

## Comandos Úteis

```bash
# Ver status de todos os serviços
docker-compose ps

# Ver logs em tempo real
docker-compose logs -f

# Reiniciar apenas o serviço web
docker-compose restart web

# Criar superusuário
docker-compose exec web python manage.py createsuperuser

# Executar migrações
docker-compose exec web python manage.py migrate
```
