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
from django.urls import reverse
from datetime import datetime, timedelta
from decimal import Decimal
import csv
import logging

from django.conf import settings
from django.contrib.auth import login, get_user_model
from django.db import transaction, IntegrityError

from .models import Socio, TipoAssinatura, DocumentoSocio, HistoricoPagamento, CobrancaAbacatePay
from .forms import SocioForm, SocioRegistroForm, SocioRegistroFormAnonymous
from socios.views import is_admin_or_manager

logger = logging.getLogger(__name__)

User = get_user_model()


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
            socio.data_associacao.strftime('%d/%m/%Y') if socio.data_associacao else '',
            socio.data_vencimento.strftime('%d/%m/%Y') if socio.data_vencimento else '',
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
        socios = socios.filter(data_associacao__isnull=False, data_associacao__gte=data_associacao_inicio)
    if data_associacao_fim:
        socios = socios.filter(data_associacao__isnull=False, data_associacao__lte=data_associacao_fim)
    
    data_vencimento_inicio = request.GET.get('data_vencimento_inicio')
    data_vencimento_fim = request.GET.get('data_vencimento_fim')
    if data_vencimento_inicio:
        socios = socios.filter(data_vencimento__isnull=False, data_vencimento__gte=data_vencimento_inicio)
    if data_vencimento_fim:
        socios = socios.filter(data_vencimento__isnull=False, data_vencimento__lte=data_vencimento_fim)
    
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
        socios = socios.filter(data_vencimento__isnull=False, data_vencimento__gte=hoje, status='ativo')
    elif pagamento_status == 'vencido':
        hoje = timezone.now().date()
        socios = socios.filter(data_vencimento__isnull=False, data_vencimento__lt=hoje)
    elif pagamento_status == 'vence_em_breve':
        hoje = timezone.now().date()
        data_limite = hoje + timedelta(days=7)
        socios = socios.filter(
            data_vencimento__isnull=False,
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


def registro_socio(request):
    """Associar-se ao clube. Se não estiver logado, cria a conta e o sócio no mesmo fluxo."""
    from types import SimpleNamespace
    from users.views.UserView import SimpleUserCreationForm

    # Logado e já tem um registro de sócio
    if request.user.is_authenticated:
        try:
            socio_existente = Socio.objects.get(usuario=request.user)
        except Socio.DoesNotExist:
            socio_existente = None

        if socio_existente:
            if socio_existente.status == 'pendente_pagamento':
                # Has a pending billing — send them back to the payment page
                return redirect('socios:pagamento_aguardando', socio_id=socio_existente.id)
            messages.info(request, 'Você já é um sócio cadastrado.')
            return redirect('socios:member_portal')

    socio_mock = SimpleNamespace(id=None, foto=None, nome_exibicao='')
    registro_socio_guest = not request.user.is_authenticated

    if request.method == 'POST':
        if registro_socio_guest:
            form_user = SimpleUserCreationForm(request.POST, prefix='user')
            form = SocioRegistroFormAnonymous(request.POST, request.FILES, prefix='socio')
            if form_user.is_valid() and form.is_valid():
                try:
                    # Save user and socio in a transaction — login() must stay OUTSIDE
                    # because it cycles the session key (DB write); if the transaction
                    # were later rolled back, that session record would disappear but
                    # request.session would still hold the new key → SessionInterrupted.
                    with transaction.atomic():
                        user = form_user.save()
                        socio = form.save(commit=False)
                        socio.usuario = user
                        socio.created_by = user
                        socio.nome_completo = (user.get_full_name() or user.first_name or '').strip()
                        socio.data_nascimento = user.data_nascimento
                        socio.telefone = (user.telefone or '').strip()
                        socio.email = (user.email or '').strip()
                        socio.data_associacao = timezone.now().date()

                        plano = socio.tipo_assinatura
                        precisa_pagar = plano and plano.valor_mensal > 0
                        socio.status = 'pendente_pagamento' if precisa_pagar else 'ativo'

                        for _ in range(5):
                            try:
                                with transaction.atomic():
                                    socio.numero_socio = ''
                                    socio.save()
                                break
                            except IntegrityError as e:
                                if 'numero_socio' in str(e) and 'unique' in str(e).lower():
                                    continue
                                raise
                        else:
                            socio.numero_socio = str(__import__('uuid').uuid4())[:8].upper()
                            socio.save()

                    # Login and external HTTP call happen AFTER the DB transaction commits
                    login(request, user)

                    if precisa_pagar:
                        return _redirecionar_para_pagamento(request, socio, plano)

                    messages.success(request, f'Conta e cadastro realizados com sucesso! Bem-vindo(a), {socio.nome_exibicao}.')
                    return redirect('socios:member_portal')
                except Exception as e:
                    messages.error(request, f'Erro ao salvar: {str(e)}')
            else:
                for f in (form_user, form):
                    for field, errors in (f.errors or {}).items():
                        field_obj = f.fields.get(field)
                        label = field_obj.label if field_obj else field
                        for error in errors:
                            messages.error(request, f'{label}: {error}')
        else:
            form = SocioRegistroForm(request.POST, request.FILES)
            form_user = None
            if form.is_valid():
                try:
                    with transaction.atomic():
                        socio = form.save(commit=False)
                        socio.usuario = request.user
                        socio.created_by = request.user
                        socio.data_associacao = timezone.now().date()

                        plano = socio.tipo_assinatura
                        precisa_pagar = plano and plano.valor_mensal > 0
                        socio.status = 'pendente_pagamento' if precisa_pagar else 'ativo'
                        socio.save()

                    # External HTTP call happens AFTER the DB transaction commits
                    if precisa_pagar:
                        return _redirecionar_para_pagamento(request, socio, plano)

                    messages.success(request, f'Cadastro realizado com sucesso! Bem-vindo(a), {socio.nome_exibicao}.')
                    return redirect('socios:member_portal')
                except Exception as e:
                    messages.error(request, f'Erro ao salvar: {str(e)}')
            else:
                for field, errors in form.errors.items():
                    field_obj = form.fields.get(field)
                    label = field_obj.label if field_obj else field
                    for error in errors:
                        messages.error(request, f'{label}: {error}')
    else:
        # GET
        if registro_socio_guest:
            form_user = SimpleUserCreationForm(prefix='user')
            form = SocioRegistroFormAnonymous(prefix='socio')
        else:
            form_user = None
            user = request.user
            initial = {}
            nome = (user.get_full_name() or user.first_name or '').strip()
            if nome:
                initial['nome_completo'] = nome
            if getattr(user, 'data_nascimento', None):
                initial['data_nascimento'] = user.data_nascimento.strftime('%d/%m/%Y')
            if getattr(user, 'telefone', None) and user.telefone.strip():
                initial['telefone'] = user.telefone.strip()
                initial['celular'] = user.telefone.strip()
            if user.email and user.email.strip():
                initial['email'] = user.email.strip()
            form = SocioRegistroForm(initial=initial)

    context = {
        'form': form,
        'form_user': form_user,
        'socio': socio_mock,
        'titulo': 'Associar-se ao clube',
        'action_url': reverse('socios:registro_socio'),
        'registro_socio': True,
        'registro_socio_guest': registro_socio_guest,
    }
    return render(request, 'socios/form.html', context)


def _redirecionar_para_pagamento(request, socio, tipo_assinatura, redirect_on_error='socios:registro_socio'):
    """Creates an AbacatePay billing for socio and redirects to the payment URL."""
    from .services import criar_cobranca_associacao

    protocol = settings.PROTOCOL
    host = request.get_host()
    base = f"{protocol}://{host}"

    return_url = base + reverse('socios:pagamento_aguardando', args=[socio.id])
    completion_url = base + reverse('socios:pagamento_sucesso', args=[socio.id])

    try:
        resultado = criar_cobranca_associacao(
            tipo_assinatura=tipo_assinatura,
            socio_nome=socio.nome_exibicao,
            socio_email=socio.email or '',
            socio_cpf=socio.cpf or '',
            socio_telefone=(socio.celular or socio.telefone or ''),
            return_url=return_url,
            completion_url=completion_url,
        )
    except Exception as exc:
        logger.error(
            "Erro ao criar cobrança de associação do sócio %s no AbacatePay: %s",
            socio.id,
            exc,
        )
        messages.error(
            request,
            'Não foi possível iniciar o pagamento no momento. '
            'Por favor, tente novamente ou entre em contato com o clube.',
        )
        return redirect(redirect_on_error)

    CobrancaAbacatePay.objects.create(
        socio=socio,
        billing_id=resultado['billing_id'],
        billing_url=resultado['billing_url'],
        valor=tipo_assinatura.valor_mensal,
    )

    return redirect(resultado['billing_url'])


@login_required
def renovar_assinatura(request):
    """Permite ao sócio renovar/pagar sua mensalidade via AbacatePay pelo portal."""
    try:
        socio = Socio.objects.get(usuario=request.user)
    except Socio.DoesNotExist:
        messages.error(request, 'Você não é um sócio cadastrado.')
        return redirect('dashboard')
        
    if socio.bolsista:
        messages.info(request, 'Bolsistas não possuem cobranças de mensalidade.')
        return redirect('socios:member_portal')
        
    tipo_assinatura = socio.tipo_assinatura
    if not tipo_assinatura or tipo_assinatura.valor_mensal <= 0:
        messages.info(request, 'Seu plano de sócio é gratuito ou não requer pagamento.')
        return redirect('socios:member_portal')
        
    # Prevenção de duplicidade: reusar cobrança pendente recente (criada nas últimas 24 horas)
    h24_ago = timezone.now() - timedelta(hours=24)
    cobranca_pendente = CobrancaAbacatePay.objects.filter(
        socio=socio,
        status=CobrancaAbacatePay.STATUS_PENDENTE,
        created_at__gte=h24_ago
    ).first()
    
    if cobranca_pendente:
        messages.info(request, 'Você já possui uma cobrança pendente. Redirecionando para o pagamento...')
        return redirect(cobranca_pendente.billing_url)
        
    # Se não há cobrança pendente válida, cria uma nova
    return _redirecionar_para_pagamento(
        request,
        socio,
        tipo_assinatura,
        redirect_on_error='socios:member_portal'
    )


@login_required
def member_portal(request):
    """Member self-service portal"""
    try:
        socio = Socio.objects.get(usuario=request.user)
    except Socio.DoesNotExist:
        messages.error(request, 'Você não é um sócio cadastrado')
        return redirect('dashboard')

    # Redirect to payment page if registration is pending payment
    if socio.status == 'pendente_pagamento':
        return redirect('socios:pagamento_aguardando', socio_id=socio.id)
    
    # Payment history
    pagamentos = HistoricoPagamento.objects.filter(
        socio=socio
    ).order_by('-data_pagamento')[:10]
    
    # Documents
    documentos = DocumentoSocio.objects.filter(socio=socio).order_by('-data_upload')
    
    # Payment status
    hoje = timezone.now().date()
    dias_para_vencimento = (socio.data_vencimento - hoje).days if socio.data_vencimento else None
    
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
