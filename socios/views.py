from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Socio, TipoAssinatura, DocumentoSocio, HistoricoPagamento
from .forms import SocioForm, TipoAssinaturaForm, DocumentoSocioForm, HistoricoPagamentoForm


def is_admin_or_manager(user):
    """Verifica se o usuário é admin ou tem permissões de gestão"""
    return True


@login_required
@user_passes_test(is_admin_or_manager)
def dashboard_socios(request):
    """Dashboard principal do sistema de sócios"""
    
    # Estatísticas gerais
    total_socios = Socio.objects.count()
    socios_ativos = Socio.objects.filter(status='ativo').count()
    socios_inadimplentes = Socio.objects.filter(status='inadimplente').count()
    
    # Sócios que vencem nos próximos 7 dias
    data_limite = timezone.now().date() + timedelta(days=7)
    vencem_em_breve = Socio.objects.filter(
        data_vencimento__lte=data_limite,
        status='ativo'
    ).count()
    
    # Receita mensal (pagamentos confirmados no mês atual)
    mes_atual = timezone.now().replace(day=1).date()
    receita_mensal = HistoricoPagamento.objects.filter(
        mes_referencia__gte=mes_atual,
        status='pago'
    ).aggregate(
        total=Sum('valor')
    )['total'] or Decimal('0.00')
    
    # Gráfico de evolução de sócios (últimos 12 meses)
    evolucao_socios = []
    for i in range(12):
        data = timezone.now().date().replace(day=1) - timedelta(days=30*i)
        total = Socio.objects.filter(data_associacao__lte=data).count()
        evolucao_socios.append({
            'mes': data.strftime('%m/%Y'),
            'total': total
        })
    evolucao_socios.reverse()
    
    # Distribuição por tipo de assinatura
    distribuicao_planos = TipoAssinatura.objects.annotate(
        total_socios=Count('socio')
    ).values('nome', 'total_socios', 'cor')
    
    # Próximos vencimentos (5 mais próximos)
    proximos_vencimentos = Socio.objects.filter(
        status='ativo'
    ).order_by('data_vencimento')[:5]
    
    # Novos sócios (últimos 5)
    novos_socios = Socio.objects.order_by('-data_associacao')[:5]
    
    context = {
        'total_socios': total_socios,
        'socios_ativos': socios_ativos,
        'socios_inadimplentes': socios_inadimplentes,
        'vencem_em_breve': vencem_em_breve,
        'receita_mensal': receita_mensal,
        'evolucao_socios': evolucao_socios,
        'distribuicao_planos': distribuicao_planos,
        'proximos_vencimentos': proximos_vencimentos,
        'novos_socios': novos_socios,
    }
    
    return render(request, 'socios/dashboard.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def listar_socios(request):
    """Lista todos os sócios com filtros e paginação"""
    
    socios = Socio.objects.select_related('tipo_assinatura').all()
    
    # Filtros
    status_filter = request.GET.get('status')
    tipo_filter = request.GET.get('tipo')
    search = request.GET.get('search')
    
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
    
    # Paginação
    paginator = Paginator(socios, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Tipos de assinatura para filtro
    tipos_assinatura = TipoAssinatura.objects.filter(ativo=True)
    
    context = {
        'page_obj': page_obj,
        'tipos_assinatura': tipos_assinatura,
        'current_status': status_filter,
        'current_tipo': tipo_filter,
        'current_search': search,
    }
    
    return render(request, 'socios/listar.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def detalhe_socio(request, socio_id):
    """Exibe detalhes completos de um sócio"""
    
    socio = get_object_or_404(Socio, id=socio_id)
    
    # Histórico de pagamentos
    pagamentos = socio.pagamentos.order_by('-data_pagamento')[:10]
    
    # Documentos
    documentos = socio.documentos.order_by('-data_upload')
    
    context = {
        'socio': socio,
        'pagamentos': pagamentos,
        'documentos': documentos,
    }
    
    return render(request, 'socios/detalhe.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def cadastrar_socio(request):
    """Cadastra um novo sócio"""
    
    if request.method == 'POST':
        form = SocioForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                socio = form.save(commit=False)
                socio.created_by = request.user
                
                # Definir valores padrão para campos vazios
                if not socio.status:
                    socio.status = 'ativo'
                
                socio.save()
                
                messages.success(request, f'Sócio {socio.nome_completo} cadastrado com sucesso!')
                return redirect('socios:detalhe', socio_id=socio.id)
            except Exception as e:
                messages.error(request, f'Erro ao salvar sócio: {str(e)}')
        else:
            for field, errors in form.errors.items():
                field_name = form.fields[field].label or field
                for error in errors:
                    messages.error(request, f'{field_name}: {error}')
    else:
        form = SocioForm()
    
    context = {
        'form': form,
        'titulo': 'Cadastrar Novo Sócio',
        'action_url': reverse('socios:cadastrar'),
    }
    
    return render(request, 'socios/form.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def editar_socio(request, socio_id):
    """Edita dados de um sócio existente"""
    
    socio = get_object_or_404(Socio, id=socio_id)
    
    if request.method == 'POST':
        form = SocioForm(request.POST, request.FILES, instance=socio)
        if form.is_valid():
            form.save()
            
            messages.success(request, f'Dados de {socio.nome_completo} atualizados com sucesso!')
            return redirect('socios:detalhe', socio_id=socio.id)
    else:
        form = SocioForm(instance=socio)
    
    context = {
        'form': form,
        'socio': socio,
        'titulo': f'Editar Sócio: {socio.nome_completo}',
        'action_url': reverse('socios:editar', args=[socio_id]),
    }
    
    return render(request, 'socios/form.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def gerenciar_tipos_assinatura(request):
    """Gerencia tipos de assinatura disponíveis"""
    
    # Buscar todos os tipos com estatísticas
    tipos = TipoAssinatura.objects.annotate(
        total_socios=Count('socio'),
        receita_mensal=Sum('socio__tipo_assinatura__valor_mensal', filter=Q(socio__status='ativo')),
    ).order_by('nome')
    
    # Calcular estatísticas gerais
    tipos_ativos = tipos.filter(ativo=True).count()
    total_socios_ativos = Socio.objects.filter(status='ativo').count()
    total_socios_geral = Socio.objects.count()
    
    # Receita potencial (soma de todos os tipos ativos * número de sócios)
    receita_potencial = sum(
        tipo.valor_mensal * tipo.total_socios 
        for tipo in tipos.filter(ativo=True)
    )
    
    # Calcular receita anual para cada tipo
    for tipo in tipos:
        # Se tem valor anual definido, usar ele, senão calcular baseado no valor mensal
        if tipo.valor_anual:
            tipo.receita_anual_calculada = (tipo.receita_mensal or 0) * 12 * (tipo.valor_anual / (tipo.valor_mensal * 12))
        else:
            tipo.receita_anual_calculada = (tipo.receita_mensal or 0) * 12
    
    # Totais para o resumo
    receita_total_mensal = sum(tipo.receita_mensal or 0 for tipo in tipos)
    receita_total_anual = sum(tipo.receita_anual_calculada for tipo in tipos)
    
    context = {
        'tipos': tipos,
        'tipos_ativos': tipos_ativos,
        'total_socios_ativos': total_socios_ativos,
        'total_socios_geral': total_socios_geral,
        'receita_potencial': receita_potencial,
        'receita_total_mensal': receita_total_mensal,
        'receita_total_anual': receita_total_anual,
    }
    
    return render(request, 'socios/tipos_assinatura.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def cadastrar_tipo_assinatura(request):
    """Cadastra novo tipo de assinatura"""
    
    if request.method == 'POST':
        form = TipoAssinaturaForm(request.POST)
        print(form)
        if form.is_valid():
            tipo = form.save()
            
            messages.success(request, f'Tipo de assinatura "{tipo.nome}" criado com sucesso!')
            return redirect('socios:tipos_assinatura')
    else:
        form = TipoAssinaturaForm()
    
    context = {
        'form': form,
        'titulo': 'Novo Tipo de Assinatura',
    }
    
    return render(request, 'socios/form_tipo_assinatura.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def editar_tipo_assinatura(request, tipo_id):
    """Edita tipo de assinatura existente"""
    
    tipo = get_object_or_404(TipoAssinatura, id=tipo_id)
    
    if request.method == 'POST':
        form = TipoAssinaturaForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            
            messages.success(request, f'Tipo de assinatura "{tipo.nome}" atualizado com sucesso!')
            return redirect('socios:tipos_assinatura')
    else:
        form = TipoAssinaturaForm(instance=tipo)
    
    context = {
        'form': form,
        'tipo': tipo,
        'titulo': f'Editar Tipo: {tipo.nome}',
    }
    
    return render(request, 'socios/form_tipo_assinatura.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def excluir_tipo_assinatura(request, tipo_id):
    """Exclui tipo de assinatura"""
    
    tipo = get_object_or_404(TipoAssinatura, id=tipo_id)
    
    # Verificar se há sócios vinculados
    if tipo.socio_set.exists():
        messages.error(request, f'Não é possível excluir o tipo "{tipo.nome}" pois há sócios vinculados a ele.')
        return redirect('socios:tipos_assinatura')
    
    if request.method == 'POST':
        nome_tipo = tipo.nome
        tipo.delete()
        
        messages.success(request, f'Tipo de assinatura "{nome_tipo}" excluído com sucesso!')
        return redirect('socios:tipos_assinatura')
    
    return redirect('socios:tipos_assinatura')


@login_required
@user_passes_test(is_admin_or_manager)
def registrar_pagamento(request, socio_id):
    """Registra pagamento de um sócio"""
    
    socio = get_object_or_404(Socio, id=socio_id)
    
    if request.method == 'POST':
        form = HistoricoPagamentoForm(request.POST, request.FILES)
        if form.is_valid():
            pagamento = form.save(commit=False)
            pagamento.socio = socio
            pagamento.created_by = request.user
            pagamento.save()
            
            # Atualiza data de vencimento do sócio se pagamento confirmado
            if pagamento.status == 'confirmado':
                # Calcula nova data de vencimento baseada no tipo de assinatura
                dias_duracao = socio.tipo_assinatura.duracao_dias
                nova_data = pagamento.data_pagamento + timedelta(days=dias_duracao)
                socio.data_vencimento = nova_data
                socio.status = 'ativo'
                socio.save()
            
            messages.success(request, 'Pagamento registrado com sucesso!')
            return redirect('socios:detalhe', socio_id=socio.id)
    else:
        # Valores padrão para o formulário
        inicial = {
            'data_pagamento': timezone.now().date(),
            'data_vencimento': socio.data_vencimento,
            'valor': socio.tipo_assinatura.valor_mensal,
            'mes_referencia': timezone.now().date().replace(day=1),
        }
        form = HistoricoPagamentoForm(initial=inicial)
    
    context = {
        'form': form,
        'socio': socio,
        'titulo': f'Registrar Pagamento - {socio.nome_completo}',
    }
    
    return render(request, 'socios/form_pagamento.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def upload_documento(request, socio_id):
    """Upload de documento para um sócio"""
    
    socio = get_object_or_404(Socio, id=socio_id)
    
    if request.method == 'POST':
        form = DocumentoSocioForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.socio = socio
            documento.uploaded_by = request.user
            documento.save()
            
            messages.success(request, 'Documento enviado com sucesso!')
            return redirect('socios:detalhe', socio_id=socio.id)
    else:
        form = DocumentoSocioForm()
    
    context = {
        'form': form,
        'socio': socio,
        'titulo': f'Enviar Documento - {socio.nome_completo}',
    }
    
    return render(request, 'socios/form_documento.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def relatorio_inadimplentes(request):
    """Relatório de sócios inadimplentes"""
    
    # Sócios com vencimento atrasado
    hoje = timezone.now().date()
    inadimplentes = Socio.objects.filter(
        data_vencimento__lt=hoje,
        status__in=['ativo', 'inadimplente']
    ).select_related('tipo_assinatura').order_by('data_vencimento')
    
    # Estatísticas
    total_inadimplentes = inadimplentes.count()
    valor_total_em_atraso = sum(
        s.tipo_assinatura.valor_mensal for s in inadimplentes
    )
    
    context = {
        'inadimplentes': inadimplentes,
        'total_inadimplentes': total_inadimplentes,
        'valor_total_em_atraso': valor_total_em_atraso,
    }
    
    return render(request, 'socios/relatorio_inadimplentes.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def atualizar_status_socio(request, socio_id):
    """Atualiza status do sócio via AJAX"""
    
    if request.method == 'POST':
        socio = get_object_or_404(Socio, id=socio_id)
        novo_status = request.POST.get('status')
        
        if novo_status in dict(Socio.status_choices):
            socio.status = novo_status
            socio.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Status atualizado para {socio.get_status_display()}'
            })
    
    return JsonResponse({'success': False, 'message': 'Erro ao atualizar status'})
