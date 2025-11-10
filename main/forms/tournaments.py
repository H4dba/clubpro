from django import forms
from ..models import Tournament, Participant, Match
from django.contrib.auth import get_user_model
from django.utils import timezone

class TournamentForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        help_text="Select players to participate in the tournament"
    )

    class Meta:
        model = Tournament
        fields = [
            'name', 'description', 'tournament_type', 
            'clock_limit', 'clock_increment', 'tournament_speed',
            'start_time', 'is_private', 'min_rating', 'max_rating',
            'password', 'minutes'
        ]
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show internal tournament types for new tournaments
        if not self.instance.pk:
            self.fields['tournament_type'].choices = [
                ('internal_swiss', 'Suíço (Interno)'),
                ('internal_round_robin', 'Round Robin (Interno)')
            ]

    def clean_start_time(self):
        start_time = self.cleaned_data.get('start_time')
        if start_time and start_time < timezone.now():
            raise forms.ValidationError("Start time must be in the future")
        return start_time

class MatchResultForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['result']
        widgets = {
            'result': forms.Select(
                attrs={'class': 'form-select'},
                choices=[
                    ('pending', 'Pendente'),
                    ('white_win', 'Vitória Brancas'),
                    ('black_win', 'Vitória Pretas'),
                    ('draw', 'Empate'),
                    ('forfeit_white', 'WO Brancas'),
                    ('forfeit_black', 'WO Pretas'),
                ]
            )
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If this is a bye match, only show bye as option
        if self.instance and self.instance.black_player is None:
            self.fields['result'].widget.choices = [('bye', 'Bye')]