from django.urls import path
from . import views

app_name = 'socios'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_socios, name='dashboard'),
    
    # CRUD Sócios
    path('listar/', views.listar_socios, name='listar'),
    path('cadastrar/', views.cadastrar_socio, name='cadastrar'),
    path('<int:socio_id>/', views.detalhe_socio, name='detalhe'),
    path('<int:socio_id>/editar/', views.editar_socio, name='editar'),
    path('<int:socio_id>/status/', views.atualizar_status_socio, name='atualizar_status'),
    
    # Pagamentos
    path('<int:socio_id>/pagamento/', views.registrar_pagamento, name='registrar_pagamento'),
    
    # Documentos
    path('<int:socio_id>/documento/', views.upload_documento, name='upload_documento'),
    
    # Tipos de Assinatura
    path('tipos/', views.gerenciar_tipos_assinatura, name='tipos_assinatura'),
    path('tipos/cadastrar/', views.cadastrar_tipo_assinatura, name='cadastrar_tipo'),
    path('tipos/<int:tipo_id>/editar/', views.editar_tipo_assinatura, name='editar_tipo'),
    path('tipos/<int:tipo_id>/excluir/', views.excluir_tipo_assinatura, name='excluir_tipo'),
    
    # Relatórios
    path('relatorios/inadimplentes/', views.relatorio_inadimplentes, name='relatorio_inadimplentes'),
]