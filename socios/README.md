# Sistema de Sócios - ClubPro

Sistema completo de gerenciamento de sócios para clubes de xadrez, desenvolvido em Django com design moderno e responsivo.

## 🎯 Funcionalidades

### 📋 Dashboard
- Visão geral com estatísticas de sócios
- Alertas de vencimentos próximos
- Lista de novos sócios
- Gráficos de distribuição por planos
- Cards informativos com métricas importantes

### 👥 Gestão de Sócios
- Cadastro completo de sócios com foto
- Edição de dados pessoais e de contato
- Informações de xadrez (ratings FIDE/nacional, categoria)
- Status automático baseado em pagamentos
- Sistema de numeração automática

### 💰 Gestão Financeira
- Tipos de assinatura personalizáveis
- Histórico completo de pagamentos
- Controle de vencimentos
- Alertas de inadimplência
- Relatórios financeiros

### 📄 Documentos
- Upload de documentos por sócio
- Categorização de tipos de documento
- Visualização e download de arquivos
- Controle de acesso

### 🔧 Administração
- Interface administrativa completa
- Filtros e busca avançada
- Ações em lote
- Exportação para CSV
- Estatísticas detalhadas

## 🚀 Como Usar

### 1. Executar as Migrações
```bash
python manage.py migrate
```

### 2. Popular com Dados de Exemplo
```bash
# Criar tipos de assinatura e sócios de exemplo
python manage.py popular_socios --socios 25

# Ou limpar dados existentes e recriar
python manage.py popular_socios --socios 25 --clear
```

### 3. Carregar Fixtures (Alternativa)
```bash
python manage.py loaddata tipos_assinatura.json
```

### 4. Criar Superusuário (se necessário)
```bash
python manage.py createsuperuser
```

### 5. Executar o Servidor
```bash
python manage.py runserver
```

## 📱 Navegação

### URLs Principais
- **Dashboard**: `/socios/` - Visão geral do sistema
- **Lista de Sócios**: `/socios/listar/` - Listagem completa com filtros
- **Novo Sócio**: `/socios/cadastrar/` - Formulário de cadastro
- **Detalhes**: `/socios/<id>/` - Visualização detalhada
- **Editar**: `/socios/<id>/editar/` - Edição de dados
- **Admin**: `/admin/` - Interface administrativa

### Menu de Navegação
O sistema está integrado à navbar principal com:
- Link direto para "Sócios" no menu principal
- Acesso rápido às funcionalidades principais
- Design consistente com o restante do sistema

## 🎨 Design System

### Cores Principais
- **Primary**: `#2c3e50` (Azul escuro)
- **Gold**: `#f1c40f` (Dourado)
- **Success**: `#27ae60` (Verde)
- **Warning**: `#f39c12` (Laranja)
- **Danger**: `#e74c3c` (Vermelho)

### Componentes
- Cards modernos com sombras suaves
- Botões com animações hover
- Formulários estilizados com Bootstrap 5
- Tabelas responsivas
- Modals para confirmações
- Badges de status coloridos

## 🔧 Estrutura Técnica

### Models
1. **TipoAssinatura**: Planos de pagamento
2. **Socio**: Dados principais dos sócios
3. **DocumentoSocio**: Arquivos anexos
4. **HistoricoPagamento**: Controle financeiro

### Views
- Dashboard com estatísticas
- CRUD completo para sócios
- Sistema de paginação e filtros
- Relatórios e exportações

### Forms
- Formulários Django com validação
- Máscaras para CPF e telefone
- Upload de arquivos
- Campos condicionais

### Templates
- Base template moderno
- Design responsivo
- Componentes reutilizáveis
- Animações CSS

## 📊 Funcionalidades Avançadas

### Sistema de Status
- **Ativo**: Pagamentos em dia
- **Inadimplente**: Pagamentos em atraso
- **Suspenso**: Temporariamente inativo
- **Inativo**: Não renovado

### Filtros e Buscas
- Busca por nome, CPF ou número
- Filtros por status e plano
- Ordenação personalizada
- Paginação otimizada

### Relatórios
- Lista de inadimplentes
- Relatório de vencimentos
- Estatísticas por plano
- Exportação CSV

## 🛡️ Segurança

### Validações
- CPF único por sócio
- Validação de e-mail
- Campos obrigatórios
- Formatos de data

### Permissões
- Sistema integrado ao Django Auth
- Controle de acesso por grupo
- Logs de atividades (admin)

## 🎯 Próximos Passos

### Funcionalidades Planejadas
- [ ] Sistema de e-mail automático
- [ ] Integração com WhatsApp
- [ ] Geração de carteirinhas
- [ ] Relatórios em PDF
- [ ] Dashboard analítico
- [ ] App mobile (PWA)

### Integrações Futuras
- [ ] Gateway de pagamento
- [ ] Sistema de torneios
- [ ] Lichess API
- [ ] Backup automático

## 🔍 Comandos Úteis

### Desenvolvimento
```bash
# Ver logs do servidor
python manage.py runserver --verbosity=2

# Fazer backup do banco
python manage.py dumpdata socios > backup_socios.json

# Restaurar backup
python manage.py loaddata backup_socios.json

# Limpar cache
python manage.py collectstatic --clear
```

### Administração
```bash
# Verificar inconsistências
python manage.py check

# Ver migrações pendentes
python manage.py showmigrations

# Shell interativo
python manage.py shell
```

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs do Django
2. Consulte a documentação do Django
3. Teste em ambiente de desenvolvimento
4. Verifique permissões de arquivo (uploads)

---

**ClubPro** - Sistema de Gestão para Clubes de Xadrez
Desenvolvido com ❤️ usando Django 5.1.6