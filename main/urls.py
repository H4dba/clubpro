from django.urls import path
from .views.tournaments import tournament_dashboard, tournament_create, tournament_detail, match_result, tournament_edit

app_name = 'main'

urlpatterns = [
    path('tournaments/', tournament_dashboard, name='tournament_dashboard'),
    path('tournaments/create/', tournament_create, name='tournament_create'),
    path('tournaments/<int:pk>/', tournament_detail, name='tournament_detail'),
    path('tournaments/<int:pk>/edit/', tournament_edit, name='tournament_edit'),
    path('tournaments/<int:tournament_pk>/matches/<int:match_pk>/result/', match_result, name='match_result'),
]