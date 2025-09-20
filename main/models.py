from django.db import models
from django.conf import settings

class Tournament(models.Model):
    TOURNAMENT_TYPES = [
        ('arena', 'Arena'),
        ('swiss', 'Swiss'),
    ]
    
    TOURNAMENT_SPEEDS = [
        ('ultraBullet', 'Ultra Bullet'),
        ('bullet', 'Bullet'),
        ('blitz', 'Blitz'),
        ('rapid', 'Rapid'),
        ('classical', 'Classical'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    tournament_type = models.CharField(max_length=10, choices=TOURNAMENT_TYPES)
    clock_limit = models.IntegerField(help_text="Initial time in minutes")
    clock_increment = models.IntegerField(help_text="Increment in seconds")
    minutes = models.IntegerField(help_text="Tournament duration in minutes")
    tournament_speed = models.CharField(max_length=20, choices=TOURNAMENT_SPEEDS)
    start_time = models.DateTimeField()
    lichess_id = models.CharField(max_length=100, blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_private = models.BooleanField(default=False)
    min_rating = models.IntegerField(null=True, blank=True)
    max_rating = models.IntegerField(null=True, blank=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('created', 'Created on Lichess'),
            ('started', 'Started'),
            ('finished', 'Finished'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('main:tournament_detail', args=[str(self.id)])