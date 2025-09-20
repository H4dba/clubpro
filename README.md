# ClubPro - Sistema de Gestão para Clubes de Xadrez

## 📋 Sobre o Projeto

O ClubPro é uma plataforma web desenvolvida em Django para gestão completa de clubes de xadrez. O sistema oferece ferramentas para gerenciamento de sócios, organização de torneios e eventos, com foco especial na integração com a plataforma Lichess para torneios online.

## 🎯 Objetivos

- **Gestão de Clubes**: Ferramenta completa para administração de clubes de xadrez
- **Gerenciamento de Sócios**: Controle de membros, mensalidades e dados dos associados
- **Torneios Online**: Integração direta com Lichess para criar e gerenciar torneios
- **Eventos e Atividades**: Organização de eventos, aulas e atividades do clube
- **Futuro**: Expansão para torneios presenciais com sistema de pareamento

## ✨ Funcionalidades Atuais

### 👥 Gestão de Sócios
- Cadastro e gerenciamento de membros
- Controle de mensalidades e pagamentos
- Histórico de participações em torneios
- Perfis personalizados com integração Lichess

### 🏆 Torneios e Eventos
- Criação de torneios no Lichess via API
- Gerenciamento de inscrições
- Acompanhamento de resultados em tempo real
- Dashboard com estatísticas dos jogadores
- Calendário de eventos do clube

### 🔐 Sistema de Usuários
- Autenticação personalizada
- Diferentes níveis de acesso (Admin, Organizador, Sócio)
- Integração OAuth com Lichess
- Dashboard personalizado por tipo de usuário

## 🛠️ Tecnologias Utilizadas

- **Backend**: Django 5.1.6 (Python)
- **Banco de Dados**: SQLite3 (desenvolvimento) / PostgreSQL (produção)
- **Frontend**: HTML5, CSS3, JavaScript com Bootstrap
- **Integração**: API Lichess com Berserk
- **Autenticação**: OAuth 2.0 (Lichess)
- **Dependências**: django-widget-tweaks, django-cors-headers

## 📦 Instalação e Configuração

### Pré-requisitos
- Python 3.11+
- pip
- Git
- Conta no Lichess (para integração)

### Instalação

1. **Clone o repositório**
   ```bash
   git clone https://github.com/H4dba/clubpro.git
   cd clubpro
   ```

2. **Crie um ambiente virtual**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente**
   Crie um arquivo `.env` na raiz do projeto:
   ```env
   SECRET_KEY=sua_chave_secreta_django
   DEBUG=True
   LICHESS_CLIENT_ID=seu_client_id_lichess
   LICHESS_CLIENT_SECRET=seu_client_secret_lichess
   LICHESS_REDIRECT_URI=http://localhost:8000/users/lichess-callback/
   ```

5. **Configure o banco de dados**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Crie um superusuário**
   ```bash
   python manage.py createsuperuser
   ```

7. **Execute o servidor**
   ```bash
   python manage.py runserver
   ```

8. **Acesse a aplicação**
   Abra seu navegador em `http://localhost:8000`

## 🔧 Configuração do Lichess

Para integrar com o Lichess:

1. Acesse [Lichess OAuth Apps](https://lichess.org/account/oauth/app)
2. Crie uma nova aplicação
3. Configure:
   - **Name**: Nome do seu clube
   - **Redirect URI**: `http://localhost:8000/users/lichess-callback/`
   - **Permissions**: Marque as permissões necessárias
4. Copie o Client ID e Client Secret para o arquivo `.env`

## 📁 Estrutura do Projeto

```
clubpro/
├── clubpro/                # Configurações principais do Django
│   ├── settings.py         # Configurações do projeto
│   ├── urls.py            # URLs principais
│   └── wsgi.py            # Configuração WSGI
├── users/                  # App de gerenciamento de usuários e sócios
│   ├── models.py          # Modelos de usuário personalizado
│   ├── views/             # Views de autenticação e perfil
│   └── templates/         # Templates de login, registro, dashboard
├── lichess/               # App de integração com Lichess
│   ├── models.py          # Modelos para dados do Lichess
│   └── services.py        # Serviços de API do Lichess
├── main/                  # App principal para torneios e eventos
│   ├── models.py          # Modelos de torneios e eventos
│   ├── views/             # Views de torneios
│   ├── forms/             # Formulários de criação de torneios
│   └── templates/         # Templates de torneios
├── services/              # Serviços externos e integrações
│   ├── LichessService.py  # Serviço principal do Lichess
│   └── lichess_oauth.py   # Autenticação OAuth
├── requirements.txt       # Dependências do projeto
└── manage.py             # Script de gerenciamento Django
```

## 🚀 Como Usar

### Para Administradores de Clube
1. Faça login como superusuário
2. Configure as informações do clube
3. Cadastre os sócios
4. Crie e gerencie torneios
5. Monitore atividades e estatísticas

### Para Sócios
1. Registre-se na plataforma
2. Conecte sua conta Lichess
3. Inscreva-se em torneios
4. Acompanhe seu desempenho
5. Participe de eventos do clube

## 🎯 Roadmap - Próximas Funcionalidades

### 📅 Curto Prazo
- [ ] Sistema completo de mensalidades
- [ ] Relatórios de atividades do clube
- [ ] Notificações por email
- [ ] Chat/fórum interno

### 🏟️ Médio Prazo - Torneios Presenciais
- [ ] Sistema de pareamento Swiss/Round Robin
- [ ] Controle de tempo e arbitragem
- [ ] Impressão de tabelas e resultados
- [ ] Integração com rating FIDE/CBX

### 🚀 Longo Prazo
- [ ] App mobile
- [ ] Sistema de reserva de tabuleiros
- [ ] Gestão financeira completa
- [ ] Múltiplos clubes por instalação

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 📧 Suporte e Contato

- **Desenvolvedor**: Guilherme Hadba
- **GitHub**: [@H4dba](https://github.com/H4dba)
- **Repositório**: [https://github.com/H4dba/clubpro](https://github.com/H4dba/clubpro)

---

**ClubPro** - Transformando a gestão de clubes de xadrez com tecnologia moderna! ♟️
