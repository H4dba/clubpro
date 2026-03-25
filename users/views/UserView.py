from urllib.parse import quote
import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from services.ChessComService import ChessComApi


class SimpleUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Senha', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Confirmação de senha', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label='Nome', max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='E-mail', required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    data_nascimento = forms.DateField(
        label='Data de Nascimento',
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    telefone = forms.CharField(label='Telefone', max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    chesscom_username = forms.CharField(
        label='Usuário Chess.com',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu nome de usuário no Chess.com (opcional)',
        }),
    )

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'email', 'data_nascimento', 'telefone', 'chesscom_username')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("As senhas não coincidem")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email

    def clean_chesscom_username(self):
        username = (self.cleaned_data.get("chesscom_username") or "").strip()
        if username and not ChessComApi.username_exists(username):
            raise forms.ValidationError("Esse usuário não foi encontrado no Chess.com.")
        if username:
            from users.models import ChessComProfile
            if ChessComProfile.objects.filter(chesscom_username__iexact=username).exists():
                raise forms.ValidationError("Esse usuário do Chess.com já está vinculado a outra conta.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self._build_unique_username(self.cleaned_data.get("email", ""))
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

    def _build_unique_username(self, email: str) -> str:
        base = (email.split("@")[0] if email else "").strip().lower()
        base = re.sub(r"[^a-z0-9_]+", "_", base).strip("_")
        if not base:
            base = "user"

        UserModel = get_user_model()
        username = base[:150]
        suffix = 1
        while UserModel.objects.filter(username=username).exists():
            suffix_str = str(suffix)
            username = f"{base[:150-len(suffix_str)-1]}_{suffix_str}"
            suffix += 1
        return username


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autofocus': True}),
    )

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            UserModel = get_user_model()
            user_obj = UserModel.objects.filter(email__iexact=email).first()
            resolved_username = user_obj.username if user_obj else ""
            self.user_cache = authenticate(self.request, username=resolved_username, password=password)

            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class AdminUserChessComForm(forms.ModelForm):
    chesscom_username = forms.CharField(
        label='Usuário Chess.com',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nick no Chess.com'}),
    )

    class Meta:
        model = get_user_model()
        fields = ('chesscom_username',)

    def clean_chesscom_username(self):
        username = (self.cleaned_data.get('chesscom_username') or '').strip()
        if not username:
            return ''

        from users.models import ChessComProfile

        conflict = ChessComProfile.objects.filter(
            chesscom_username__iexact=username
        ).exclude(user=self.instance).exists()
        if conflict:
            raise forms.ValidationError('Esse usuário do Chess.com já está vinculado a outra conta.')

        if not ChessComApi.username_exists(username):
            raise forms.ValidationError('Esse usuário não foi encontrado no Chess.com.')

        return username


class AdminUserEditForm(forms.ModelForm):
    """Form abrangente para edição de usuários pelo admin."""

    first_name = forms.CharField(
        label='Nome',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    last_name = forms.CharField(
        label='Sobrenome',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        label='E-mail',
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    username = forms.CharField(
        label='Nome de usuário',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    telefone = forms.CharField(
        label='Telefone',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(21) 99999-9999'}),
    )
    data_nascimento = forms.DateField(
        label='Data de Nascimento',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    is_active = forms.BooleanField(
        label='Conta ativa',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    is_staff = forms.BooleanField(
        label='Staff (acesso admin)',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    is_superuser = forms.BooleanField(
        label='Superusuário',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    chesscom_username = forms.CharField(
        label='Usuário Chess.com',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nick no Chess.com'}),
    )
    new_password = forms.CharField(
        label='Nova senha',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        help_text='Deixe em branco para não alterar a senha.',
    )
    new_password_confirm = forms.CharField(
        label='Confirmar nova senha',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    class Meta:
        model = get_user_model()
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'telefone', 'data_nascimento',
            'is_active', 'is_staff', 'is_superuser',
            'chesscom_username',
        )

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if email:
            qs = get_user_model().objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Já existe outro usuário com este e-mail.')
        return email

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if username:
            qs = get_user_model().objects.filter(username__iexact=username).exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Já existe outro usuário com esse nome de usuário.')
        return username

    def clean_chesscom_username(self):
        username = (self.cleaned_data.get('chesscom_username') or '').strip()
        if not username:
            return ''

        from users.models import ChessComProfile
        conflict = ChessComProfile.objects.filter(
            chesscom_username__iexact=username
        ).exclude(user=self.instance).exists()
        if conflict:
            raise forms.ValidationError('Esse usuário do Chess.com já está vinculado a outra conta.')

        if not ChessComApi.username_exists(username):
            raise forms.ValidationError('Esse usuário não foi encontrado no Chess.com.')

        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('new_password_confirm')
        if p1 or p2:
            if p1 != p2:
                self.add_error('new_password_confirm', 'As senhas não coincidem.')
        return cleaned_data


class CustomLoginView(LoginView):
    template_name = "login.html"
    form_class = EmailAuthenticationForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse('dashboard')


def _is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def register_view(request):
    """View para registro de novos usuários"""
    if request.method == "POST":
        form = SimpleUserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    chesscom_username = form.cleaned_data.get('chesscom_username')
                    if chesscom_username:
                        _connect_chesscom_for_user(user, chesscom_username)
                    login(request, user)
                    messages.success(request, 'Registro realizado com sucesso!')
                    return redirect('dashboard')
            except ValidationError as e:
                form.add_error('chesscom_username', e.message)
            except IntegrityError:
                form.add_error('chesscom_username', 'Esse usuário do Chess.com já está vinculado a outra conta.')
    else:
        form = SimpleUserCreationForm()

    return render(request, "register.html", {"form": form})


def landing_page(request):
    """Página inicial do sistema"""
    from main.models import Tournament

    recent_tournaments = Tournament.objects.filter(
        status__in=['in_progress', 'finished']
    ).order_by('-start_time')[:3]
    
    featured_products = []
    try:
        from shop.models import Product
        featured_products = Product.objects.filter(
            is_active=True,
            is_featured=True
        )[:3]
    except Exception:
        pass
    
    address = settings.AXM_MAPS_ADDRESS
    q = quote(address)
    maps_open_url = f'https://www.google.com/maps/search/?api=1&query={q}'
    maps_embed_src = settings.GOOGLE_MAPS_EMBED_SRC or (
        f'https://maps.google.com/maps?q={q}&hl=pt-BR&z=17&output=embed'
    )

    context = {
        'recent_tournaments': recent_tournaments,
        'featured_products': featured_products,
        'axm_maps_address': address,
        'maps_open_url': maps_open_url,
        'maps_embed_src': maps_embed_src,
    }

    return render(request, "landing-page.html", context)


def custom_logout(request):
    """Logout personalizado que redireciona para a página inicial"""
    logout(request)
    return redirect('landing-page')


@login_required
def dashboard(request):
    """Dashboard principal do usuário com informações do Chess.com"""
    from users.models import ChessComProfile

    context = {
        'user': request.user,
    }

    try:
        perfil = ChessComProfile.objects.get(user=request.user)
        context['perfil_chesscom'] = perfil
    except ChessComProfile.DoesNotExist:
        context['perfil_chesscom'] = None

    top_players_profiles = ChessComProfile.objects.filter(
        user__is_chesscom_connected=True,
        rapid_rating__isnull=False
    ).select_related('user').order_by('-rapid_rating')[:10]
    
    top_players = []
    for perfil in top_players_profiles:
        top_players.append({
            'username': perfil.user.username,
            'chesscom_username': perfil.chesscom_username,
            'rapid_rating': perfil.rapid_rating,
            'blitz_rating': perfil.blitz_rating,
            'bullet_rating': perfil.bullet_rating,
        })

    context['top_players'] = top_players
    return render(request, 'dashboard.html', context)


@login_required
def admin_users_list(request):
    """Página administrativa para listar usuários do sistema."""
    if not _is_admin_user(request.user):
        messages.error(request, 'Você não tem permissão para acessar esta área.')
        return redirect('dashboard')

    query = (request.GET.get('q') or '').strip()
    users_qs = get_user_model().objects.all().order_by('username')

    if query:
        users_qs = users_qs.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(email__icontains=query) |
            Q(chesscom_username__icontains=query)
        )

    paginator = Paginator(users_qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin_users.html', {
        'page_obj': page_obj,
        'query': query,
    })


@login_required
def admin_user_edit(request, user_id):
    """Página administrativa para editar dados de um usuário."""
    if not _is_admin_user(request.user):
        messages.error(request, 'Você não tem permissão para acessar esta área.')
        return redirect('dashboard')

    target_user = get_object_or_404(get_user_model(), id=user_id)

    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, instance=target_user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)

                    new_password = form.cleaned_data.get('new_password')
                    if new_password:
                        user.set_password(new_password)

                    user.save()

                    chesscom_username = form.cleaned_data.get('chesscom_username')
                    current_chesscom = target_user.chesscom_username

                    if chesscom_username and chesscom_username.lower() != (current_chesscom or '').lower():
                        _connect_chesscom_for_user(user, chesscom_username)
                    elif not chesscom_username and current_chesscom:
                        from users.models import ChessComProfile
                        user.chesscom_username = None
                        user.is_chesscom_connected = False
                        user.save(update_fields=['chesscom_username', 'is_chesscom_connected'])
                        ChessComProfile.objects.filter(user=user).delete()

                messages.success(request, f'Usuário {user.username} atualizado com sucesso.')
                return redirect('admin_user_edit', user_id=user.id)
            except ValidationError as e:
                form.add_error('chesscom_username', e.message)
            except Exception as exc:
                messages.error(request, f'Erro ao salvar: {exc}')
    else:
        form = AdminUserEditForm(instance=target_user)

    from users.models import ChessComProfile
    chesscom_profile = ChessComProfile.objects.filter(user=target_user).first()

    return render(request, 'admin_user_edit.html', {
        'target_user': target_user,
        'form': form,
        'chesscom_profile': chesscom_profile,
    })


@login_required
def conectar_chesscom(request):
    """Permite ao usuário vincular / alterar o username do Chess.com"""
    if request.method == 'POST':
        chesscom_username = (request.POST.get('chesscom_username') or '').strip()
        if not chesscom_username:
            messages.error(request, 'Informe seu nome de usuário no Chess.com.')
            return redirect('dashboard')

        if not ChessComApi.username_exists(chesscom_username):
            messages.error(request, f'Usuário "{chesscom_username}" não encontrado no Chess.com.')
            return redirect('dashboard')

        try:
            _connect_chesscom_for_user(request.user, chesscom_username)
            messages.success(request, f'Conectado ao Chess.com como {chesscom_username}!')
        except ValidationError as e:
            messages.error(request, e.message)
        except Exception:
            messages.error(request, 'Não foi possível obter as estatísticas do Chess.com. Tente novamente.')

    return redirect('dashboard')


@login_required
def atualizar_dados_chesscom(request):
    """Atualiza os dados do usuário a partir do Chess.com"""
    if not request.user.is_chesscom_connected or not request.user.chesscom_username:
        messages.error(request, 'Você precisa estar conectado ao Chess.com para atualizar os dados.')
        return redirect('dashboard')

    try:
        _connect_chesscom_for_user(request.user, request.user.chesscom_username)
        messages.success(request, 'Dados do Chess.com atualizados com sucesso!')
    except Exception:
        messages.error(request, 'Falha ao atualizar dados do Chess.com. Tente novamente.')

    return redirect('dashboard')


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _connect_chesscom_for_user(user, chesscom_username: str) -> None:
    """Fetch Chess.com stats and persist them."""
    from users.models import ChessComProfile

    normalized_username = (chesscom_username or "").strip()
    if not normalized_username:
        raise ValidationError('Informe um usuário Chess.com válido.')

    profile_in_use = ChessComProfile.objects.filter(chesscom_username__iexact=normalized_username).exclude(user=user).exists()
    if profile_in_use:
        raise ValidationError('Esse usuário do Chess.com já está vinculado a outra conta.')

    stats = ChessComApi.get_player_stats(normalized_username)
    if stats is None:
        raise ValidationError('Não foi possível obter as estatísticas do Chess.com para esse usuário.')

    user.chesscom_username = normalized_username
    user.is_chesscom_connected = True
    user.save(update_fields=['chesscom_username', 'is_chesscom_connected'])

    perfil, _ = ChessComProfile.objects.update_or_create(
        user=user,
        defaults={'chesscom_username': normalized_username},
    )
    perfil.atualizar_de_api(stats)
