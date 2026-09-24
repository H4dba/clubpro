from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path(
        "esqueci-senha/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
            success_url="/users/esqueci-senha/enviado/",
        ),
        name="password_reset",
    ),
    path(
        "esqueci-senha/enviado/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "redefinir-senha/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url="/users/redefinir-senha/concluido/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "redefinir-senha/concluido/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("logout/", custom_logout, name="logout"),
    path("register/", register_view, name="register"),
    path("landing-page/", landing_page, name="landing-page"),
    path('conectar-chesscom/', conectar_chesscom, name='conectar_chesscom'),
    path('atualizar-chesscom/', atualizar_dados_chesscom, name='atualizar_dados_chesscom'),
    path('admin/usuarios/', admin_users_list, name='admin_users_list'),
    path('admin/usuarios/<int:user_id>/editar/', admin_user_edit, name='admin_user_edit'),
    path('dashboard/', dashboard, name='dashboard'),
]
