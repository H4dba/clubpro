from django import forms
from ..models import Tournament
from django.utils import timezone

class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = [
            'name', 'description', 'tournament_type',
            'clock_limit', 'clock_increment', 'minutes',
            'tournament_speed', 'start_time', 'is_private',
            'min_rating', 'max_rating', 'password'
        ]
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_start_time(self):
        start_time = self.cleaned_data.get('start_time')
        if start_time and start_time < timezone.now():
            raise forms.ValidationError("Start time must be in the future")
        return start_time