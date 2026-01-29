# Guia de Deploy em Produção - AXM ClubPro

Este guia descreve como fazer o deploy da aplicação em produção usando Docker.

## Pré-requisitos

- Servidor com Docker e Docker Compose instalados
- Domínio configurado apontando para o servidor
- Certificado SSL (Let's Encrypt recomendado)

## 1. Preparação do Servidor

### Instalar Docker e Docker Compose

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 2. Configuração de Variáveis de Ambiente

Crie um arquivo `.env` no servidor com as seguintes variáveis:

```env
# Database Configuration
DB_NAME=clubpro_db
DB_USER=clubpro_user
DB_PASSWORD=SUA_SENHA_FORTE_AQUI
DB_HOST=db
DB_PORT=5432
DB_ENGINE=django.db.backends.postgresql

# Django Settings
SECRET_KEY=SUA_SECRET_KEY_MUITO_FORTE_AQUI_GERE_UMA_NOVA
DEBUG=False
ALLOWED_HOSTS=seudominio.com,www.seudominio.com
HOST=seudominio.com

# Lichess Configuration (se aplicável)
LICHESS_CLIENT_ID=https://seudominio.com
LICHESS_CLIENT_SECRET=seu-lichess-secret
```

### Gerar SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 3. Configuração SSL

### Opção 1: Let's Encrypt (Recomendado)

```bash
# Instalar Certbot
sudo apt-get update
sudo apt-get install certbot

# Gerar certificado
sudo certbot certonly --standalone -d seudominio.com -d www.seudominio.com

# Copiar certificados para o diretório do projeto
sudo mkdir -p /caminho/do/projeto/ssl
sudo cp /etc/letsencrypt/live/seudominio.com/fullchain.pem /caminho/do/projeto/ssl/cert.pem
sudo cp /etc/letsencrypt/live/seudominio.com/privkey.pem /caminho/do/projeto/ssl/key.pem
sudo chmod 644 /caminho/do/projeto/ssl/cert.pem
sudo chmod 600 /caminho/do/projeto/ssl/key.pem
```

### Opção 2: Certificado Próprio

Coloque seus certificados em:
- `ssl/cert.pem` - Certificado
- `ssl/key.pem` - Chave privada

## 4. Ajustar nginx.conf

Edite o `nginx.conf` e atualize o `server_name` com seu domínio:

```nginx
server_name seudominio.com www.seudominio.com;
```

## 5. Deploy

```bash
# Clonar repositório (se ainda não tiver)
git clone <seu-repositorio> /caminho/do/projeto
cd /caminho/do/projeto

# Criar arquivo .env com as variáveis acima
nano .env

# Construir e iniciar serviços
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Verificar logs
docker-compose -f docker-compose.prod.yml logs -f
```

## 6. Criar Superusuário

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## 7. Verificações Pós-Deploy

### Verificar se está funcionando

```bash
# Status dos containers
docker-compose -f docker-compose.prod.yml ps

# Logs do Django
docker-compose -f docker-compose.prod.yml logs web

# Logs do Nginx
docker-compose -f docker-compose.prod.yml logs nginx

# Testar conexão com banco
docker-compose -f docker-compose.prod.yml exec db psql -U $DB_USER -d $DB_NAME
```

### Verificar segurança

- [ ] DEBUG=False no .env
- [ ] SECRET_KEY forte e única
- [ ] ALLOWED_HOSTS configurado corretamente
- [ ] SSL funcionando (https://)
- [ ] Senhas do banco fortes
- [ ] Arquivos estáticos sendo servidos pelo Nginx

## 8. Manutenção

### Atualizar código

```bash
git pull
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Backup do banco de dados

```bash
# Criar backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
docker-compose -f docker-compose.prod.yml exec -T db psql -U $DB_USER $DB_NAME < backup.sql
```

### Renovar certificado SSL (Let's Encrypt)

```bash
# Renovar certificado
sudo certbot renew

# Copiar novos certificados
sudo cp /etc/letsencrypt/live/seudominio.com/fullchain.pem /caminho/do/projeto/ssl/cert.pem
sudo cp /etc/letsencrypt/live/seudominio.com/privkey.pem /caminho/do/projeto/ssl/key.pem

# Reiniciar Nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

## 9. Monitoramento

### Logs

```bash
# Todos os logs
docker-compose -f docker-compose.prod.yml logs -f

# Apenas erros
docker-compose -f docker-compose.prod.yml logs web | grep ERROR
```

### Recursos

```bash
# Uso de recursos
docker stats

# Espaço em disco
df -h
docker system df
```

## 10. Troubleshooting

### Container não inicia

```bash
docker-compose -f docker-compose.prod.yml logs web
docker-compose -f docker-compose.prod.yml exec web python manage.py check
```

### Erro 502 Bad Gateway

- Verificar se o serviço web está rodando
- Verificar logs do Nginx
- Verificar conectividade entre Nginx e Django

### Erro de conexão com banco

- Verificar variáveis de ambiente
- Verificar se o banco está saudável: `docker-compose -f docker-compose.prod.yml ps db`
- Verificar logs do banco: `docker-compose -f docker-compose.prod.yml logs db`

## Segurança Adicional

1. **Firewall**: Configure UFW ou iptables para permitir apenas portas 80 e 443
2. **Fail2Ban**: Instale para proteger contra ataques de força bruta
3. **Backups Automáticos**: Configure cron jobs para backups regulares
4. **Monitoramento**: Considere usar ferramentas como Prometheus/Grafana
5. **Updates**: Mantenha Docker e imagens atualizadas

## Suporte

Para problemas ou dúvidas, consulte:
- Logs: `docker-compose -f docker-compose.prod.yml logs`
- Status: `docker-compose -f docker-compose.prod.yml ps`
- Django check: `docker-compose -f docker-compose.prod.yml exec web python manage.py check`
