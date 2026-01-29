"""
Enhanced views for socios management
Bulk actions, advanced filtering, exports, member portal
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Count, Sum, F
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta
from decimal import Decimal
import csv

from .models import Socio, TipoAssinatura, DocumentoSocio, HistoricoPagamento
from .forms import SocioForm
from socios.views import is_admin_or_manager


@login_required
@user_passes_test(is_admin_or_manager)
@require_POST
def bulk_status_update(request):
    """Bulk update status for multiple socios"""
    socio_ids = request.POST.getlist('socio_ids')
    new_status = request.POST.get('new_status')
    
    if not socio_ids:
        messages.error(request, 'Nenhum sócio selecionado')
        return redirect('socios:listar')
    
    if not new_status:
        messages.error(request, 'Status não especificado')
        return redirect('socios:listar')
    
    valid_statuses = ['ativo', 'inadimplente', 'suspenso', 'inativo']
    if new_status not in valid_statuses:
        messages.error(request, 'Status inválido')
        return redirect('socios:listar')
    
    updated = Socio.objects.filter(id__in=socio_ids).update(status=new_status)
    messages.success(request, f'{updated} sócio(s) atualizado(s) com sucesso!')
    
    return redirect('socios:listar')


@login_required
@user_passes_test(is_admin_or_manager)
def export_socios_csv(request):
    """Export socios to CSV"""
    socios = Socio.objects.select_related('tipo_assinatura').all()
    
    # Apply filters from request
    status_filter = request.GET.get('status')
    tipo_filter = request.GET.get('plano')
    search = request.GET.get('busca')
    
    if status_filter:
        socios = socios.filter(status=status_filter)
    if tipo_filter:
        socios = socios.filter(tipo_assinatura_id=tipo_filter)
    if search:
        socios = socios.filter(
            Q(nome_completo__icontains=search) |
            Q(nome_social__icontains=search) |
            Q(numero_socio__icontains=search) |
            Q(email__icontains=search) |
            Q(cpf__icontains=search)
        )
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="socios_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Número Sócio', 'Nome Completo', 'Nome Social', 'CPF', 'Email',
        'Telefone', 'Status', 'Tipo Assinatura', 'Data Associação',
        'Data Vencimento', 'Rating FIDE', 'Rating CBX', 'Cidade', 'Estado'
    ])
    
    for socio in socios:
        writer.writerow([
            socio.numero_socio,
            socio.nome_completo,
            socio.nome_social or '',
            socio.cpf,
            socio.email,
            socio.telefone or socio.celular or '',
            socio.get_status_display(),
            socio.tipo_assinatura.nome if socio.tipo_assinatura else '',
            socio.data_associacao.strftime('%d/%m/%Y'),
            socio.data_vencimento.strftime('%d/%m/%Y'),
            socio.rating_fide or '',
            socio.rating_cbx or '',
            socio.cidade,
            socio.estado,
        ])
    
    return response


@login_required
@user_passes_test(is_admin_or_manager)
def advanced_search(request):
    """Advanced search with multiple filters"""
    socios = Socio.objects.select_related('tipo_assinatura').all()
    
    # Text search
    search_query = request.GET.get('q', '')
    if search_query:
        socios = socios.filter(
            Q(nome_completo__icontains=search_query) |
            Q(nome_social__icontains=search_query) |
            Q(numero_socio__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(cpf__icontains=search_query) |
            Q(telefone__icontains=search_query) |
            Q(celular__icontains=search_query)
        )
    
    # Status filter
    status = request.GET.get('status')
    if status:
        socios = socios.filter(status=status)
    
    # Plan filter
    plano_id = request.GET.get('plano')
    if plano_id:
        socios = socios.filter(tipo_assinatura_id=plano_id)
    
    # Date filters
    data_associacao_inicio = request.GET.get('data_associacao_inicio')
    data_associacao_fim = request.GET.get('data_associacao_fim')
    if data_associacao_inicio:
        socios = socios.filter(data_associacao__gte=data_associacao_inicio)
    if data_associacao_fim:
        socios = socios.filter(data_associacao__lte=data_associacao_fim)
    
    data_vencimento_inicio = request.GET.get('data_vencimento_inicio')
    data_vencimento_fim = request.GET.get('data_vencimento_fim')
    if data_vencimento_inicio:
        socios = socios.filter(data_vencimento__gte=data_vencimento_inicio)
    if data_vencimento_fim:
        socios = socios.filter(data_vencimento__lte=data_vencimento_fim)
    
    # Location filters
    cidade = request.GET.get('cidade')
    if cidade:
        socios = socios.filter(cidade__icontains=cidade)
    
    estado = request.GET.get('estado')
    if estado:
        socios = socios.filter(estado=estado)
    
    # Rating filters
    rating_fide_min = request.GET.get('rating_fide_min')
    rating_fide_max = request.GET.get('rating_fide_max')
    if rating_fide_min:
        socios = socios.filter(rating_fide__gte=rating_fide_min)
    if rating_fide_max:
        socios = socios.filter(rating_fide__lte=rating_fide_max)
    
    # Payment status
    pagamento_status = request.GET.get('pagamento_status')
    if pagamento_status == 'em_dia':
        hoje = timezone.now().date()
        socios = socios.filter(data_vencimento__gte=hoje, status='ativo')
    elif pagamento_status == 'vencido':
        hoje = timezone.now().date()
        socios = socios.filter(data_vencimento__lt=hoje)
    elif pagamento_status == 'vence_em_breve':
        hoje = timezone.now().date()
        data_limite = hoje + timedelta(days=7)
        socios = socios.filter(
            data_vencimento__gte=hoje,
            data_vencimento__lte=data_limite,
            status='ativo'
        )
    
    # Pagination
    paginator = Paginator(socios, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Context
    tipos_assinatura = TipoAssinatura.objects.filter(ativo=True)
    estados = Socio.objects.values_list('estado', flat=True).distinct().order_by('estado')
    
    context = {
        'socios': page_obj,
        'tipos_assinatura': tipos_assinatura,
        'estados': estados,
        'filters': {
            'q': search_query,
            'status': status,
            'plano': plano_id,
            'data_associacao_inicio': data_associacao_inicio,
            'data_associacao_fim': data_associacao_fim,
            'data_vencimento_inicio': data_vencimento_inicio,
            'data_vencimento_fim': data_vencimento_fim,
            'cidade': cidade,
            'estado': estado,
            'rating_fide_min': rating_fide_min,
            'rating_fide_max': rating_fide_max,
            'pagamento_status': pagamento_status,
        }
    }
    
    return render(request, 'socios/advanced_search.html', context)


@login_required
def member_portal(request):
    """Member self-service portal"""
    try:
        socio = Socio.objects.get(usuario=request.user)
    except Socio.DoesNotExist:
        messages.error(request, 'Você não é um sócio cadastrado')
        return redirect('dashboard')
    
    # Payment history
    pagamentos = HistoricoPagamento.objects.filter(
        socio=socio
    ).order_by('-data_pagamento')[:10]
    
    # Documents
    documentos = DocumentoSocio.objects.filter(socio=socio).order_by('-data_upload')
    
    # Payment status
    hoje = timezone.now().date()
    dias_para_vencimento = (socio.data_vencimento - hoje).days
    
    context = {
        'socio': socio,
        'pagamentos': pagamentos,
        'documentos': documentos,
        'dias_para_vencimento': dias_para_vencimento,
        'situacao_pagamento': socio.situacao_pagamento,
    }
    
    return render(request, 'socios/member_portal.html', context)


@login_required
def member_update_info(request):
    """Allow members to update their own information"""
    try:
        socio = Socio.objects.get(usuario=request.user)
    except Socio.DoesNotExist:
        messages.error(request, 'Você não é um sócio cadastrado')
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Allow updating certain fields only
        socio.telefone = request.POST.get('telefone', socio.telefone)
        socio.celular = request.POST.get('celular', socio.celular)
        socio.email = request.POST.get('email', socio.email)
        socio.endereco = request.POST.get('endereco', socio.endereco)
        socio.numero = request.POST.get('numero', socio.numero)
        socio.complemento = request.POST.get('complemento', socio.complemento)
        socio.bairro = request.POST.get('bairro', socio.bairro)
        socio.cidade = request.POST.get('cidade', socio.cidade)
        socio.estado = request.POST.get('estado', socio.estado)
        socio.cep = request.POST.get('cep', socio.cep)
        socio.aceita_emails = request.POST.get('aceita_emails') == 'on'
        socio.aceita_whatsapp = request.POST.get('aceita_whatsapp') == 'on'
        socio.save()
        
        messages.success(request, 'Informações atualizadas com sucesso!')
        return redirect('socios:member_portal')
    
    return render(request, 'socios/member_update_info.html', {'socio': socio})
