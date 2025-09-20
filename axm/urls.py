"""
URL configuration for axm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from users.views.UserView import landing_page
from users.views.UserView import CustomLoginView
from main import views as main_views


urlpatterns = [
    path('', landing_page),
    path('admin/', admin.site.urls),
    path("users/", include("users.urls")),
    path("accounts/login/", CustomLoginView.as_view(), name="login"),
    path('tournament-manager/', main_views.tournament_dashboard, name='tournament_dashboard'),
    path('tournament-manager/create/', main_views.tournament_create, name='tournament_create'),
    path('tournament-manager/<int:pk>/edit/', main_views.tournament_edit, name='tournament_edit'),
    
]
