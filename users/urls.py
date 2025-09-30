from django.urls import path
from .views import *
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", custom_logout, name="logout"),
    path("register/", register_view, name="register"),
    path("landing-page/", landing_page, name="landing-page"),
    #path("user_info/", teste_lichess, name="teste_lichess"),
    path('connect-lichess/', connect_lichess, name='connect_lichess'),
    path('lichess-callback/', lichess_callback, name='lichess_callback'),
    path('atualizar-lichess/', atualizar_dados_lichess, name='atualizar_dados_lichess'),
    path('dashboard/', dashboard, name='dashboard'),
]
