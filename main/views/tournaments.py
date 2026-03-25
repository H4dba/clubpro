from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model
from ..models import Tournament
from ..forms import TournamentForm

def is_tournament_manager(user):
    return user.is_authenticated

@user_passes_test(is_tournament_manager)
def tournament_dashboard(request):
    tournaments = Tournament.objects.all().order_by('-start_time')
    return render(request, 'tournament_dashboard.html', {
        'tournaments': tournaments
    })

@user_passes_test(is_tournament_manager)
def tournament_create(request):
    if request.method == 'POST':
        form = TournamentForm(request.POST, request.FILES)
        if form.is_valid():
            tournament = form.save(commit=False)
            tournament.created_by = request.user
            tournament.status = 'pending'
            tournament.save()
            
            participants = form.cleaned_data.get('participants', [])
            for user in participants:
                tournament.participants.create(player=user, name=f"__user_{user.id}__")
            
            messages.success(request, 'Torneio criado com sucesso!')
            return redirect('main:tournament_detail', pk=tournament.id)
    else:
        form = TournamentForm()
    
    return render(request, 'tournament_form.html', {
        'form': form,
        'title': 'Create Tournament'
    })

@user_passes_test(is_tournament_manager)
def tournament_detail(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    
    available_users = get_user_model().objects.exclude(
        id__in=tournament.participants.filter(player__isnull=False).values_list('player_id', flat=True)
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_participants':
            participant_ids = request.POST.getlist('participants')
            for user_id in participant_ids:
                user = get_user_model().objects.get(id=user_id)
                tournament.participants.create(player=user, name=f"__user_{user.id}__")
            messages.success(request, 'Players added successfully!')
            
        elif action == 'add_unregistered_player':
            player_name = request.POST.get('player_name')
            player_rating = request.POST.get('player_rating')
            if player_name:
                if not tournament.participants.filter(name=player_name).exists():
                    tournament.participants.create(
                        name=player_name,
                        rating=player_rating if player_rating else None
                    )
                    messages.success(request, f'{player_name} added successfully!')
                else:
                    messages.error(request, f'A player with the name {player_name} is already registered')
            
        elif action == 'remove_participant':
            participant_id = request.POST.get('participant_id')
            if participant_id:
                tournament.participants.filter(id=participant_id).delete()
                messages.success(request, 'Player removed successfully!')
                
        return redirect('main:tournament_detail', pk=pk)
    
    standings = tournament.participants.all().order_by('-score')
    
    return render(request, 'tournament_detail.html', {
        'tournament': tournament,
        'standings': standings,
        'available_users': available_users,
    })


@user_passes_test(is_tournament_manager)
def tournament_edit(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    if tournament.status != 'pending':
        messages.error(request, 'Only pending tournaments can be edited.')
        return redirect('main:tournament_dashboard')
        
    if request.method == 'POST':
        form = TournamentForm(request.POST, request.FILES, instance=tournament)
        if form.is_valid():
            tournament = form.save()
            
            if form.cleaned_data.get('participants'):
                tournament.participants.all().delete()
                for user in form.cleaned_data['participants']:
                    tournament.participants.create(player=user, name=f"__user_{user.id}__")
            
            messages.success(request, 'Tournament updated successfully!')
            return redirect('main:tournament_detail', pk=tournament.id)
    else:
        form = TournamentForm(instance=tournament)
        form.fields['participants'].initial = [p.player.id for p in tournament.participants.all()]
    
    return render(request, 'tournament_form.html', {
        'form': form,
        'tournament': tournament,
        'title': 'Edit Tournament'
    })
