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

    # Obtém o perfil Lichess do usuário se existir
    from users.models import LichessProfile
    try:
        perfil_lichess = LichessProfile.objects.get(user=request.user)
        context['perfil_lichess'] = perfil_lichess
    except LichessProfile.DoesNotExist:
        context['perfil_lichess'] = None

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

    # Obtém os melhores jogadores para o ranking usando LichessProfile
    from users.models import LichessProfile
    top_players_profiles = LichessProfile.objects.filter(
        user__is_lichess_connected=True,
        rapid_rating__isnull=False
    ).select_related('user').order_by('-rapid_rating')[:10]
    
    # Converte para uma lista de dados formatados
    top_players = []
    for perfil in top_players_profiles:
        top_players.append({
            'username': perfil.user.username,
            'rapid_rating': perfil.rapid_rating,
            'blitz_rating': perfil.blitz_rating,
            'bullet_rating': perfil.bullet_rating,
            'classical_rating': perfil.classical_rating,
        })

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
    """Callback para processar a resposta da autorização do Lichess (Lichess OAuth)"""
    codigo = request.GET.get('code')
    erro = request.GET.get('error')
    descricao_erro = request.GET.get('error_description')

    if erro or not codigo:
        messages.error(request, f'Falha na autorização: {descricao_erro or "Nenhum código recebido"}')
        return redirect('dashboard')

    oauth = LichessOAuth()
    try:
        # Obtém o token de acesso usando PKCE
        token_acesso = oauth.get_access_token(request, codigo)
        print(f"Token de acesso recebido: {token_acesso[:10]}...")  # Log de depuração

        # Inicializa API do Lichess com o novo token
        lichess_api = LichessApi(token_acesso)

        # Obtém dados do usuário e trata resposta em lista
        dados_usuario_lista = lichess_api.get_user_info(request.user.username)
        print(f"Dados do usuário: {dados_usuario_lista}")  # Log de depuração

        # Obtém o primeiro item se for uma lista
        dados_usuario = dados_usuario_lista[0] if isinstance(dados_usuario_lista, list) else dados_usuario_lista

        if dados_usuario and 'perfs' in dados_usuario:
            print('Salvando token e perfil do usuário')
            # Atualiza informações básicas do usuário
            request.user.lichess_id = dados_usuario.get('id')
            request.user.lichess_access_token = token_acesso
            request.user.is_lichess_connected = True
            request.user.save()

            # Atualiza ou cria o perfil Lichess
            from users.models import LichessProfile
            perfil, criado = LichessProfile.objects.get_or_create(user=request.user)
            perfil.lichess_id = dados_usuario.get('id')
            perfs = dados_usuario['perfs']
            # Ratings e jogos
            perfil.bullet_rating = perfs.get('bullet', {}).get('rating')
            perfil.bullet_games_played = perfs.get('bullet', {}).get('games')
            perfil.blitz_rating = perfs.get('blitz', {}).get('rating')
            perfil.blitz_games_played = perfs.get('blitz', {}).get('games')
            perfil.rapid_rating = perfs.get('rapid', {}).get('rating')
            perfil.rapid_games_played = perfs.get('rapid', {}).get('games')
            perfil.classical_rating = perfs.get('classical', {}).get('rating')
            perfil.classical_games_played = perfs.get('classical', {}).get('games')
            # Puzzles
            perfil.puzzles_rating = perfs.get('puzzle', {}).get('rating')
            perfil.puzzles_solved = perfs.get('puzzle', {}).get('games')
            perfil.save()
            messages.success(request, 'Conectado ao Lichess e perfil atualizado com sucesso!')
        else:
            messages.error(request, f'Falha ao buscar dados do usuário no Lichess. Resposta: {dados_usuario}')

    except Exception as e:
        messages.error(request, f'Falha ao conectar com o Lichess: {str(e)}')
        print(f"Detalhes da exceção: {str(e)}")  # Log de depuração

    return redirect('dashboard')


@login_required
def atualizar_dados_lichess(request):
    """Atualiza os dados do usuário a partir do Lichess"""
    if not request.user.is_lichess_connected:
        messages.error(request, 'Você precisa estar conectado ao Lichess para atualizar os dados.')
        return redirect('dashboard')
    
    if not request.user.lichess_access_token:
        messages.error(request, 'Token de acesso não encontrado. Reconecte sua conta Lichess.')
        return redirect('dashboard')
    
    try:
        # Inicializa API do Lichess com o token do usuário
        lichess_api = LichessApi(request.user.lichess_access_token)
        
        # Obtém dados atualizados do usuário
        dados_usuario_lista = lichess_api.get_user_info(request.user.username)
        dados_usuario = dados_usuario_lista[0] if isinstance(dados_usuario_lista, list) else dados_usuario_lista
        
        if dados_usuario and 'perfs' in dados_usuario:
            # Atualiza ou cria o perfil Lichess
            from users.models import LichessProfile
            perfil, criado = LichessProfile.objects.get_or_create(user=request.user)
            
            # Atualiza informações básicas
            perfil.lichess_id = dados_usuario.get('id')
            perfs = dados_usuario['perfs']
            
            # Atualiza ratings e jogos para todos os controles de tempo
            perfil.bullet_rating = perfs.get('bullet', {}).get('rating')
            perfil.bullet_games_played = perfs.get('bullet', {}).get('games')
            perfil.blitz_rating = perfs.get('blitz', {}).get('rating')
            perfil.blitz_games_played = perfs.get('blitz', {}).get('games')
            perfil.rapid_rating = perfs.get('rapid', {}).get('rating')
            perfil.rapid_games_played = perfs.get('rapid', {}).get('games')
            perfil.classical_rating = perfs.get('classical', {}).get('rating')
            perfil.classical_games_played = perfs.get('classical', {}).get('games')
            
            # Atualiza dados de puzzles
            perfil.puzzles_rating = perfs.get('puzzle', {}).get('rating')
            perfil.puzzles_solved = perfs.get('puzzle', {}).get('games')
            
            perfil.save()
            
            messages.success(request, 'Dados do Lichess atualizados com sucesso!')
        else:
            messages.error(request, 'Falha ao buscar dados atualizados do Lichess.')
            
    except Exception as e:
        messages.error(request, f'Erro ao atualizar dados do Lichess: {str(e)}')
        print(f"Erro na atualização: {str(e)}")  # Log de depuração
    
    return redirect('dashboard')