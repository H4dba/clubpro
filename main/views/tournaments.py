from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from ..models import Tournament
from ..forms import TournamentForm
from services.LichessService import LichessApi

def is_tournament_manager(user):
    return user.is_authenticated

@user_passes_test(is_tournament_manager)
def tournament_dashboard(request):
    tournaments = Tournament.objects.all().order_by('-start_time')
    print(tournaments)
    return render(request, 'tournament_dashboard.html', {
        'tournaments': tournaments
    })

@user_passes_test(is_tournament_manager)
def tournament_create(request):
    if request.method == 'POST':
        form = TournamentForm(request.POST)
        if form.is_valid():
            print('Form is valid')
            tournament = form.save(commit=False)
            tournament.created_by = request.user
            
            try:

                lichess_api = LichessApi(request.user.lichess_access_token)
                tournament_data = {
                    'name': tournament.name,
                    'clock_limit': tournament.clock_limit,  # This will be in minutes
                    'clock_increment': tournament.clock_increment,
                    'minutes': tournament.minutes,  # This will be used as nb_rounds
                    'start_time': tournament.start_time,
                    'description': tournament.description,
                }
                
                print(tournament_data)
                lichess_response = lichess_api.create_tournament(tournament_data)
                print(lichess_response)
                # Save the Lichess tournament ID and update status
                tournament.lichess_id = lichess_response['id']
                tournament.status = 'created'
                tournament.save()
                
                messages.success(request, 'Tournament created successfully!')
                return redirect('tournament_dashboard')
                
            except Exception as e:
                messages.error(request, f'Failed to create tournament on Lichess: {str(e)}')
    else:
        form = TournamentForm()
    
    return render(request, 'tournament_form.html', {
        'form': form,
        'title': 'Create Tournament'
    })

@user_passes_test(is_tournament_manager)
def tournament_edit(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    
    if request.method == 'POST':
        form = TournamentForm(request.POST, instance=tournament)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tournament updated successfully!')
            return redirect('tournament_dashboard')
    else:
        form = TournamentForm(instance=tournament)
    
    return render(request, 'tournament_form.html', {
        'form': form,
        'tournament': tournament,
        'title': 'Edit Tournament'
    })