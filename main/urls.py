from django.urls import path
from .views.tournaments import tournament_dashboard, tournament_create, tournament_detail, tournament_edit

app_name = 'main'

urlpatterns = [
    path('tournaments/', tournament_dashboard, name='tournament_dashboard'),
    path('tournaments/create/', tournament_create, name='tournament_create'),
    path('tournaments/<int:pk>/', tournament_detail, name='tournament_detail'),
    path('tournaments/<int:pk>/edit/', tournament_edit, name='tournament_edit'),

]