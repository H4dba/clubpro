from django.shortcuts import render

from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout

from services import LichessApi




class CustomLoginView(LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True
    login_redirect_url = 'accounts/test'

def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            request.session["pending_user_id"] = user.id

            return redirect(reverse("lichess_login"))

    else:
        form = UserCreationForm()

    return render(request, "register.html", {"form": form})

def landing_page(request):
    return render(request, "landing-page.html")

def custom_logout(request):
    logout(request)
    return redirect('landing-page')

def dashboard(request):
    print()


def teste_lichess(request):
    lichess_client = LichessApi()
    print(lichess_client.get_user_info('H4dba'))