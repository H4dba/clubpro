from django.urls import path
from .views.torneios_views import (
    torneios_lista,
    torneios_detalhe,
    torneios_inscrever,
    torneios_desinscrever,
    torneios_gerenciar,
    torneios_anunciar,
    torneios_editar,
    torneios_inscritos,
    torneios_iniciar,
    torneios_confirmar_pagamento,
)

app_name = 'torneios'

urlpatterns = [
    path('', torneios_lista, name='lista'),
    path('<int:pk>/', torneios_detalhe, name='detalhe'),
    path('<int:pk>/inscrever/', torneios_inscrever, name='inscrever'),
    path('<int:pk>/desinscrever/', torneios_desinscrever, name='desinscrever'),
    path('gerenciar/', torneios_gerenciar, name='gerenciar'),
    path('gerenciar/anunciar/', torneios_anunciar, name='anunciar'),
    path('gerenciar/<int:pk>/editar/', torneios_editar, name='editar'),
    path('gerenciar/<int:pk>/inscritos/', torneios_inscritos, name='inscritos'),
    path('gerenciar/<int:torneio_pk>/inscritos/<int:participant_pk>/confirmar_pagamento/', torneios_confirmar_pagamento, name='confirmar_pagamento'),
    path('gerenciar/<int:pk>/iniciar/', torneios_iniciar, name='iniciar'),
]
