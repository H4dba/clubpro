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

# Custom form without email requirement
class SimpleUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ('username',)

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
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
    if request.method == "POST":
        form = SimpleUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Connect your Lichess account to access all features.')
            return redirect('dashboard')
    else:
        form = SimpleUserCreationForm()

    return render(request, "register.html", {"form": form})

def landing_page(request):
    return render(request, "landing-page.html")

def custom_logout(request):
    logout(request)
    return redirect('landing-page')

@login_required
def dashboard(request):
    User = get_user_model()
    context = {
        'user': request.user,
    }
    print(request.user.lichess_access_token)

    if request.user.is_lichess_connected:
        # Initialize API with user's token
        lichess_api = LichessApi(request.user.lichess_access_token)
        
        # Get fresh user data
        user_data = lichess_api.get_user_info(request.user.username)
        recent_games = lichess_api.get_user_games(request.user.username, max_games=5)
        current_games = lichess_api.get_user_current_games(request.user.username)
        
        context.update({
            'lichess_data': user_data,
            'recent_games': recent_games,
            'current_games': current_games,
        })

    # Get top players for leaderboard
    top_players = User.objects.filter(
        is_lichess_connected=True
    ).exclude(
        lichess_rating_rapid__isnull=True
    ).order_by('-lichess_rating_rapid')[:10]

    context['top_players'] = top_players
    return render(request, 'dashboard.html', context)

@login_required
def connect_lichess(request):
    oauth = LichessOAuth()
    auth_url = oauth.get_authorization_url(request)
    return redirect(auth_url)

@login_required
def lichess_callback(request):
    code = request.GET.get('code')
    error = request.GET.get('error')
    error_description = request.GET.get('error_description')

    if error or not code:
        messages.error(request, f'Authorization failed: {error_description or "No code received"}')
        return redirect('dashboard')

    oauth = LichessOAuth()
    try:
        # Get access token using PKCE
        access_token = oauth.get_access_token(request, code)
        print(f"Received access token: {access_token[:10]}...") # Debug print
        
        # Initialize Lichess API with the new token
        lichess_api = LichessApi(access_token)
        
        # Get user data and handle list response
        user_data_list = lichess_api.get_user_info(request.user.username)
        print(f"User data: {user_data_list}")  # Debug print
        
        # Get the first item if it's a list
        user_data = user_data_list[0] if isinstance(user_data_list, list) else user_data_list
        
        if user_data and 'perfs' in user_data:
            print('salvando user_token')
            # Update user's Lichess information
            request.user.lichess_id = user_data.get('id')
            request.user.lichess_access_token = access_token
            request.user.is_lichess_connected = True
            
            # Update ratings from perfs
            perfs = user_data['perfs']
            request.user.lichess_rating_bullet = perfs.get('bullet', {}).get('rating')
            request.user.lichess_rating_blitz = perfs.get('blitz', {}).get('rating')
            request.user.lichess_rating_rapid = perfs.get('rapid', {}).get('rating')
            request.user.lichess_rating_classical = perfs.get('classical', {}).get('rating')
            
            request.user.save()
            messages.success(request, 'Successfully connected to Lichess!')
        else:
            messages.error(request, f'Failed to fetch Lichess user data. Response: {user_data}')
            
    except Exception as e:
        messages.error(request, f'Failed to connect to Lichess: {str(e)}')
        print(f"Exception details: {str(e)}")  # Debug print

    return redirect('dashboard')