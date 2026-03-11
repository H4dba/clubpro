"""
Novas views para torneios: anúncios e inscrições.
Rotas em /torneios/ - separadas das antigas /tournaments/
"""
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse

from ..models import Tournament, Participant
from ..forms import TorneioAnuncioForm


def is_staff_or_superuser(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# === Público: listar e ver torneios anunciados ===

def torneios_lista(request):
    """Lista de torneios anunciados (público)."""
    agora = timezone.now()
    torneios = Tournament.objects.filter(
        status__in=['pending', 'created'],
        start_time__gte=agora
    ).order_by('start_time')
    return render(request, 'torneios/lista.html', {'torneios': torneios})


def torneios_detalhe(request, pk):
    """Detalhe do torneio com botão de inscrição (público)."""
    torneio = get_object_or_404(Tournament, pk=pk)
    inscrito = False
    if request.user.is_authenticated:
        inscrito = torneio.participants.filter(player=request.user).exists()
    pode_inscrever = (
        torneio.status == 'pending' and
        torneio.start_time > timezone.now() and
        not inscrito
    )
    return render(request, 'torneios/detalhe.html', {
        'torneio': torneio,
        'inscrito': inscrito,
        'pode_inscrever': pode_inscrever,
    })


@login_required
@require_POST
def torneios_inscrever(request, pk):
    """Inscrever-se no torneio."""
    torneio = get_object_or_404(Tournament, pk=pk)
    if torneio.status != 'pending':
        messages.error(request, 'Inscrições encerradas para este torneio.')
        return redirect('torneios:detalhe', pk=pk)
    if torneio.start_time <= timezone.now():
        messages.error(request, 'O torneio já começou.')
        return redirect('torneios:detalhe', pk=pk)
    if torneio.participants.filter(player=request.user).exists():
        messages.info(request, 'Você já está inscrito neste torneio.')
        return redirect('torneios:detalhe', pk=pk)
    Participant.objects.create(tournament=torneio, player=request.user)
    messages.success(request, f'Inscrição realizada! Você está inscrito em {torneio.name}.')
    return redirect('torneios:detalhe', pk=pk)


@login_required
@require_POST
def torneios_desinscrever(request, pk):
    """Cancelar inscrição."""
    torneio = get_object_or_404(Tournament, pk=pk)
    if torneio.status != 'pending':
        messages.error(request, 'Não é possível cancelar inscrição após o início das inscrições.')
        return redirect('torneios:detalhe', pk=pk)
    Participant.objects.filter(tournament=torneio, player=request.user).delete()
    messages.success(request, 'Inscrição cancelada.')
    return redirect('torneios:detalhe', pk=pk)


# === Gestão: ferramentas para staff ===

@user_passes_test(is_staff_or_superuser)
def torneios_gerenciar(request):
    """Painel de gestão de torneios."""
    torneios = Tournament.objects.all().order_by('-start_time')
    return render(request, 'torneios/gerenciar.html', {'torneios': torneios})


@user_passes_test(is_staff_or_superuser)
def torneios_anunciar(request):
    """Anunciar novo torneio."""
    if request.method == 'POST':
        form = TorneioAnuncioForm(request.POST)
        if form.is_valid():
            torneio = form.save(commit=False)
            torneio.created_by = request.user
            torneio.is_lichess = False
            torneio.status = 'pending'
            torneio.save()
            messages.success(request, f'Torneio "{torneio.name}" anunciado com sucesso!')
            return redirect('torneios:gerenciar')
    else:
        form = TorneioAnuncioForm()
    return render(request, 'torneios/form.html', {
        'form': form,
        'titulo': 'Anunciar Torneio',
    })


@user_passes_test(is_staff_or_superuser)
def torneios_editar(request, pk):
    """Editar torneio anunciado."""
    torneio = get_object_or_404(Tournament, pk=pk)
    if torneio.status != 'pending':
        messages.error(request, 'Apenas torneios com inscrições abertas podem ser editados.')
        return redirect('torneios:gerenciar')
    if request.method == 'POST':
        form = TorneioAnuncioForm(request.POST, instance=torneio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Torneio atualizado.')
            return redirect('torneios:gerenciar')
    else:
        form = TorneioAnuncioForm(instance=torneio)
    return render(request, 'torneios/form.html', {
        'form': form,
        'torneio': torneio,
        'titulo': 'Editar Torneio',
    })


@user_passes_test(is_staff_or_superuser)
def torneios_inscritos(request, pk):
    """Listar inscritos no torneio."""
    torneio = get_object_or_404(Tournament, pk=pk)
    inscritos = torneio.participants.all().order_by('registered_at')
    return render(request, 'torneios/inscritos.html', {
        'torneio': torneio,
        'inscritos': inscritos,
    })


@user_passes_test(is_staff_or_superuser)
@require_POST
def torneios_iniciar(request, pk):
    """Iniciar torneio (fechar inscrições e ir para gestão de partidas)."""
    torneio = get_object_or_404(Tournament, pk=pk)
    if torneio.status != 'pending':
        messages.error(request, 'Este torneio já foi iniciado ou finalizado.')
        return redirect('torneios:gerenciar')
    torneio.status = 'in_progress'
    num = torneio.participants.count()
    if torneio.tournament_type in ['swiss', 'internal_swiss']:
        torneio.total_rounds = min(num - 1, 7) if num > 1 else 0
    elif torneio.tournament_type in ['round_robin', 'internal_round_robin']:
        torneio.total_rounds = num - 1 if num % 2 == 0 else num
    torneio.save()
    messages.success(request, 'Torneio iniciado. Use a gestão de torneios para rodadas e resultados.')
    return redirect('main:tournament_detail', pk=pk)
