from django.shortcuts import render

from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from services.lichess_oauth import LichessOAuth
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from services.LichessService import LichessApi

# Formulário customizado sem exigir email
class SimpleUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Senha', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmação de senha', widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ('username',)

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("As senhas não coincidem")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class CustomLoginView(LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse('dashboard')

def register_view(request):
    """View para registro de novos usuários"""
    if request.method == "POST":
        form = SimpleUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registro realizado com sucesso! Conecte sua conta Lichess para acessar todos os recursos.')
            return redirect('dashboard')
    else:
        form = SimpleUserCreationForm()

    return render(request, "register.html", {"form": form})

def landing_page(request):
    """Página inicial do sistema"""
    return render(request, "landing-page.html")

def custom_logout(request):
    """Logout personalizado que redireciona para a página inicial"""
    logout(request)
    return redirect('landing-page')

@login_required
def dashboard(request):
    """Dashboard principal do usuário com informações do Lichess"""
    User = get_user_model()
    context = {
        'user': request.user,
    }

    if request.user.is_lichess_connected:
        # Inicializa API com o token do usuário
        lichess_api = LichessApi(request.user.lichess_access_token)
        
        try:
            # Obtém dados atualizados do usuário
            user_data = lichess_api.get_user_info(request.user.username)
            
            # Obtém e processa jogos recentes
            recent_games_data = list(lichess_api.get_user_games(request.user.username, max_games=5))
            recent_games = []
            
            for game in recent_games_data:
                game_info = {
                    'id': game['id'],
                    'white': {
                        'name': game['players']['white'].get('user', {}).get('name', 'Anonymous'),
                        'rating': game['players']['white'].get('rating', '?')
                    },
                    'black': {
                        'name': game['players']['black'].get('user', {}).get('name', 'Anonymous'),
                        'rating': game['players']['black'].get('rating', '?')
                    },
                    'winner': game.get('winner', 'draw'),
                    'status': game.get('status', ''),
                    'speed': game.get('speed', ''),
                    'timestamp': game.get('createdAt', '')
                }
                recent_games.append(game_info)
            
            # Obtém jogos atuais (se houver método disponível)
            try:
                current_games = lichess_api.get_current_games(request.user.username)
            except AttributeError:
                current_games = []  # Método pode não existir ainda
            
            
            context.update({
                'lichess_data': user_data,
                'recent_games': recent_games,
                'current_games': current_games,
            })
        except Exception as e:
            print(f"Erro ao buscar dados do Lichess: {str(e)}")
            messages.error(request, "Falha ao buscar alguns dados do Lichess")

    # Obtém os melhores jogadores para o ranking
    top_players = User.objects.filter(
        is_lichess_connected=True
    ).exclude(
        lichess_rating_rapid__isnull=True
    ).order_by('-lichess_rating_rapid')[:10]

    context['top_players'] = top_players
    return render(request, 'dashboard.html', context)

@login_required
def connect_lichess(request):
    """Inicia o processo de conexão com o Lichess via OAuth"""
    oauth = LichessOAuth()
    auth_url = oauth.get_authorization_url(request)
    return redirect(auth_url)

@login_required
def lichess_callback(request):
    """Callback para processar a resposta da autorização do Lichess"""
    code = request.GET.get('code')
    error = request.GET.get('error')
    error_description = request.GET.get('error_description')

    if error or not code:
        messages.error(request, f'Falha na autorização: {error_description or "Nenhum código recebido"}')
        return redirect('dashboard')

    oauth = LichessOAuth()
    try:
        # Obtém token de acesso usando PKCE
        access_token = oauth.get_access_token(request, code)
        print(f"Token de acesso recebido: {access_token[:10]}...")  # Log de debug
        
        # Inicializa API do Lichess com o novo token
        lichess_api = LichessApi(access_token)
        
        # Obtém dados do usuário e trata resposta em lista
        user_data_list = lichess_api.get_user_info(request.user.username)
        print(f"Dados do usuário: {user_data_list}")  # Log de debug
        
        # Obtém o primeiro item se for uma lista
        user_data = user_data_list[0] if isinstance(user_data_list, list) else user_data_list
        
        if user_data and 'perfs' in user_data:
            print('Salvando token do usuário')
            # Atualiza informações do Lichess do usuário
            request.user.lichess_id = user_data.get('id')
            request.user.lichess_access_token = access_token
            request.user.is_lichess_connected = True
            
            # Atualiza ratings dos perfs
            perfs = user_data['perfs']
            request.user.lichess_rating_bullet = perfs.get('bullet', {}).get('rating')
            request.user.lichess_rating_blitz = perfs.get('blitz', {}).get('rating')
            request.user.lichess_rating_rapid = perfs.get('rapid', {}).get('rating')
            request.user.lichess_rating_classical = perfs.get('classical', {}).get('rating')
            
            request.user.save()
            messages.success(request, 'Conectado ao Lichess com sucesso!')
        else:
            messages.error(request, f'Falha ao buscar dados do usuário no Lichess. Resposta: {user_data}')
            
    except Exception as e:
        messages.error(request, f'Falha ao conectar com o Lichess: {str(e)}')
        print(f"Detalhes da exceção: {str(e)}")  # Log de debug

    return redirect('dashboard')