# ✅ Checklist de Produção - AXM ClubPro

Use este checklist antes de fazer deploy em produção.

## 🔐 Segurança

- [ ] `DEBUG=False` no arquivo `.env`
- [ ] `SECRET_KEY` forte e única gerada (não a padrão)
- [ ] `ALLOWED_HOSTS` configurado com seu domínio real
- [ ] Senhas do banco de dados fortes e únicas
- [ ] Certificado SSL configurado e funcionando
- [ ] Headers de segurança habilitados no Nginx
- [ ] `.env` não está no repositório Git
- [ ] Arquivos sensíveis estão no `.gitignore`

## 🗄️ Banco de Dados

- [ ] PostgreSQL configurado com senha forte
- [ ] Backup automático configurado
- [ ] Migrações testadas localmente
- [ ] Dados de desenvolvimento não estão em produção

## 🌐 Configuração de Rede

- [ ] Domínio apontando para o servidor
- [ ] Portas 80 e 443 abertas no firewall
- [ ] SSL/TLS funcionando (HTTPS)
- [ ] Redirecionamento HTTP → HTTPS configurado

## 📁 Arquivos e Mídia

- [ ] `STATIC_ROOT` configurado corretamente
- [ ] `MEDIA_ROOT` configurado corretamente
- [ ] Nginx servindo arquivos estáticos
- [ ] Permissões de arquivos corretas

## 🐳 Docker

- [ ] `Dockerfile.prod` testado
- [ ] `docker-compose.prod.yml` configurado
- [ ] Variáveis de ambiente no `.env`
- [ ] Volumes persistentes configurados
- [ ] Healthchecks funcionando

## 📊 Monitoramento

- [ ] Logs sendo coletados
- [ ] Métricas de recursos configuradas
- [ ] Alertas configurados (opcional)

## 🔄 Deploy

- [ ] Código atualizado no repositório
- [ ] Testes passando
- [ ] Backup do banco antes do deploy
- [ ] Plano de rollback preparado

## ✅ Pós-Deploy

- [ ] Aplicação acessível via HTTPS
- [ ] Admin do Django funcionando
- [ ] Superusuário criado
- [ ] Arquivos estáticos sendo servidos
- [ ] Upload de mídia funcionando
- [ ] Logs sem erros críticos

## 📝 Documentação

- [ ] Credenciais documentadas (em local seguro)
- [ ] Processo de backup documentado
- [ ] Processo de restore documentado
- [ ] Contatos de emergência documentados

## 🚨 Em Caso de Problemas

1. Verificar logs: `docker-compose -f docker-compose.prod.yml logs`
2. Verificar status: `docker-compose -f docker-compose.prod.yml ps`
3. Verificar conectividade: `docker-compose -f docker-compose.prod.yml exec web python manage.py check`
4. Restaurar backup se necessário
