#!/bin/bash
# Script de deploy para produção
# Uso: ./deploy.sh

set -e

echo "🚀 Iniciando deploy em produção..."

# Verificar se o arquivo .env existe
if [ ! -f .env ]; then
    echo "❌ Erro: Arquivo .env não encontrado!"
    echo "Crie um arquivo .env baseado no .env.production.example"
    exit 1
fi

# Verificar se DEBUG está False
if grep -q "DEBUG=True" .env; then
    echo "⚠️  AVISO: DEBUG está True no .env. Certifique-se de que está False em produção!"
    read -p "Continuar mesmo assim? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Construir imagens
echo "📦 Construindo imagens Docker..."
docker compose -f docker compose.prod.yml build --no-cache

# Parar containers existentes
echo "🛑 Parando containers existentes..."
docker compose -f docker compose.prod.yml down

# Iniciar containers
echo "▶️  Iniciando containers..."
docker compose -f docker compose.prod.yml up -d

# Aguardar serviços ficarem prontos
echo "⏳ Aguardando serviços ficarem prontos..."
sleep 10

# Executar migrações
echo "🔄 Executando migrações..."
docker compose -f docker compose.prod.yml exec -T web python manage.py migrate --noinput

# Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
docker compose -f docker compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Verificar status
echo "✅ Verificando status dos containers..."
docker compose -f docker compose.prod.yml ps

echo ""
echo "✅ Deploy concluído!"
echo "📊 Ver logs com: docker compose -f docker compose.prod.yml logs -f"
echo "👤 Criar superusuário: docker compose -f docker compose.prod.yml exec web python manage.py createsuperuser"
