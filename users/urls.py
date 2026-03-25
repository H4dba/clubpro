from django.urls import path
from .views import *
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", custom_logout, name="logout"),
    path("register/", register_view, name="register"),
    path("landing-page/", landing_page, name="landing-page"),
    path('conectar-chesscom/', conectar_chesscom, name='conectar_chesscom'),
    path('atualizar-chesscom/', atualizar_dados_chesscom, name='atualizar_dados_chesscom'),
    path('admin/usuarios/', admin_users_list, name='admin_users_list'),
    path('admin/usuarios/<int:user_id>/editar/', admin_user_edit, name='admin_user_edit'),
    path('dashboard/', dashboard, name='dashboard'),
]
