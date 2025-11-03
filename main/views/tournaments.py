from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model
from ..models import Tournament, Match
from ..forms import TournamentForm, MatchResultForm
from services.LichessService import LichessApi
from ..services.tournament_pairings import generate_next_round

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
        form = TournamentForm(request.POST)
        if form.is_valid():
            tournament = form.save(commit=False)
            tournament.created_by = request.user
            
            if tournament.tournament_type.startswith('internal_'):
                tournament.is_lichess = False
                tournament.status = 'pending'
                tournament.save()
                
                # Add participants
                participants = form.cleaned_data.get('participants', [])
                for user in participants:
                    tournament.participants.create(player=user)
                
                messages.success(request, 'Tournament created successfully!')
                return redirect('main:tournament_detail', pk=tournament.id)
            else:
                try:
                    lichess_api = LichessApi(request.user.lichess_access_token)
                    tournament_data = {
                        'name': tournament.name,
                        'clock_limit': tournament.clock_limit,
                        'clock_increment': tournament.clock_increment,
                        'minutes': tournament.minutes,
                        'start_time': tournament.start_time,
                        'description': tournament.description,
                    }
                    
                    lichess_response = lichess_api.create_tournament(tournament_data)
                    tournament.lichess_id = lichess_response['id']
                    tournament.status = 'created'
                    tournament.save()
                    
                    messages.success(request, 'Tournament created successfully on Lichess!')
                    return redirect('main:tournament_dashboard')
                    
                except Exception as e:
                    messages.error(request, f'Failed to create tournament on Lichess: {str(e)}')
    else:
        form = TournamentForm()
    
    return render(request, 'tournament_form.html', {
        'form': form,
        'title': 'Create Tournament'
    })

@user_passes_test(is_tournament_manager)
def tournament_detail(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    
    # Get current matches and check if any are pending
    current_matches = Match.objects.filter(
        tournament=tournament,
        round_number=tournament.current_round
    ).order_by('board_number')
    
    # Get all past rounds matches
    past_rounds = {}
    for round_num in range(1, tournament.current_round):
        past_rounds[round_num] = Match.objects.filter(
            tournament=tournament,
            round_number=round_num
        ).order_by('board_number')
    
    has_pending_matches = current_matches.filter(result='pending').exists()

    # Get all users except those already participating
    available_users = get_user_model().objects.exclude(
        id__in=tournament.participants.filter(player__isnull=False).values_list('player_id', flat=True)
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_participants':
            participant_ids = request.POST.getlist('participants')
            for user_id in participant_ids:
                user = get_user_model().objects.get(id=user_id)
                tournament.participants.create(player=user)
            messages.success(request, 'Players added successfully!')
            
        elif action == 'add_unregistered_player':
            player_name = request.POST.get('player_name')
            player_rating = request.POST.get('player_rating')
            if player_name:
                # Check if this name is already in use
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
                
        elif action == 'start_round':
            if tournament.status == 'pending':
                tournament.status = 'in_progress'
                # Set total rounds based on number of players for Swiss tournament
                num_players = tournament.participants.count()
                if tournament.tournament_type in ['swiss', 'internal_swiss']:
                    tournament.total_rounds = min(num_players - 1, 7)  # Standard Swiss rounds limit
                elif tournament.tournament_type in ['round_robin', 'internal_round_robin']:
                    tournament.total_rounds = num_players - 1 if num_players % 2 == 0 else num_players
                tournament.save()
            
            if has_pending_matches:
                messages.error(request, 'Cannot start next round. Complete all current matches first.')
            elif tournament.current_round >= tournament.total_rounds:
                tournament.status = 'finished'
                tournament.save()
                messages.error(request, 'Tournament has reached its maximum number of rounds.')
            else:
                if generate_next_round(tournament):
                    messages.success(request, f'Round {tournament.current_round} started!')
                else:
                    messages.error(request, 'Cannot start next round. Make sure all current matches are completed.')
            
        return redirect('main:tournament_detail', pk=pk)
    
    standings = tournament.participants.all().order_by('-score', '-tiebreak_1', '-tiebreak_2')
    
    return render(request, 'tournament_detail.html', {
        'tournament': tournament,
        'current_matches': current_matches,
        'past_rounds': past_rounds,
        'standings': standings,
        'available_users': available_users,
        'has_pending_matches': has_pending_matches,
    })

@user_passes_test(is_tournament_manager)
def match_result(request, tournament_pk, match_pk):
    match = get_object_or_404(Match, pk=match_pk, tournament_id=tournament_pk)
    
    if request.method == 'POST':
        form = MatchResultForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
            messages.success(request, 'Match result recorded successfully!')
            return redirect('main:tournament_detail', pk=tournament_pk)
    else:
        form = MatchResultForm(instance=match)
    
    return render(request, 'match_result_form.html', {
        'form': form,
        'match': match,
        'tournament': match.tournament
    })

@user_passes_test(is_tournament_manager)
def tournament_edit(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    if tournament.status != 'pending':
        messages.error(request, 'Only pending tournaments can be edited.')
        return redirect('main:tournament_dashboard')
        
    if request.method == 'POST':
        form = TournamentForm(request.POST, instance=tournament)
        if form.is_valid():
            tournament = form.save()
            
            # Update participants if provided
            if form.cleaned_data.get('participants'):
                # Remove existing participants
                tournament.participants.all().delete()
                # Add new participants
                for user in form.cleaned_data['participants']:
                    tournament.participants.create(player=user)
            
            messages.success(request, 'Tournament updated successfully!')
            return redirect('main:tournament_detail', pk=tournament.id)
    else:
        form = TournamentForm(instance=tournament)
        # Pre-select current participants
        form.fields['participants'].initial = [p.player.id for p in tournament.participants.all()]
    
    return render(request, 'tournament_form.html', {
        'form': form,
        'tournament': tournament,
        'title': 'Edit Tournament'
    })