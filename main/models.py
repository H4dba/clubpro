from django.db import models
from django.conf import settings
from django.urls import reverse

class Tournament(models.Model):
    TOURNAMENT_TYPES = [
        ('arena', 'Arena'),
        ('swiss', 'Suíço'),
        ('round_robin', 'Round Robin'),
        ('internal_swiss', 'Suíço (Interno)'),
        ('internal_round_robin', 'Round Robin (Interno)'),
    ]

    TOURNAMENT_SPEEDS = [
        ('bullet', 'Bullet'),
        ('blitz', 'Blitz'),
        ('rapid', 'Rápido'),
        ('classical', 'Clássico'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('created', 'Criado'),
        ('in_progress', 'Em Andamento'),
        ('started', 'Iniciado'),
        ('finished', 'Finalizado'),
        ('cancelled', 'Cancelado'),
    ]

    name = models.CharField(max_length=100, verbose_name="Nome")
    description = models.TextField(blank=True, verbose_name="Descrição")
    tournament_type = models.CharField(max_length=20, choices=TOURNAMENT_TYPES, verbose_name="Tipo")
    tournament_speed = models.CharField(max_length=20, choices=TOURNAMENT_SPEEDS, verbose_name="Velocidade")
    clock_limit = models.IntegerField(verbose_name="Tempo Inicial (minutos)")
    clock_increment = models.IntegerField(verbose_name="Incremento (segundos)")
    minutes = models.IntegerField(verbose_name="Duração (minutos)")
    start_time = models.DateTimeField(verbose_name="Data de Início")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    external_url = models.URLField(blank=True, verbose_name="Link Externo do Torneio")
    is_private = models.BooleanField(default=False, verbose_name="Torneio Privado")
    password = models.CharField(max_length=50, blank=True, verbose_name="Senha")
    min_rating = models.IntegerField(null=True, blank=True, verbose_name="Rating Mínimo")
    max_rating = models.IntegerField(null=True, blank=True, verbose_name="Rating Máximo")
    is_online = models.BooleanField(default=False, verbose_name="Torneio Online")
    prize = models.TextField(blank=True, verbose_name="Premiação")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Valor da Inscrição")
    rules_pdf = models.FileField(upload_to='tournament_rules/', blank=True, null=True, verbose_name="Regulamento (PDF)")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('main:tournament_detail', args=[str(self.id)])

    class Meta:
        verbose_name = "Torneio"
        verbose_name_plural = "Torneios"
        ordering = ['-start_time']

class Participant(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='participants')
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100, blank=True, verbose_name="Nome")  # For unregistered players
    rating = models.IntegerField(null=True, blank=True, verbose_name="Rating")  # For unregistered players
    score = models.FloatField(default=0)
    registered_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    payment_confirmed = models.BooleanField(default=False, verbose_name="Pagamento Confirmado")

    class Meta:
        unique_together = [
            ('tournament', 'player'),  # Only for registered players
            ('tournament', 'name'),    # Only for unregistered players
        ]
        ordering = ['-score']
        verbose_name = "Participante"
        verbose_name_plural = "Participantes"

    def __str__(self):
        if self.player:
            return f"{self.player.username} - {self.tournament.name}"
        return f"{self.name} - {self.tournament.name}"

    def get_display_name(self):
        return self.player.username if self.player else self.name

class Match(models.Model):
    RESULT_CHOICES = [
        ('pending', 'Pendente'),
        ('white_win', 'Vitória Brancas'),
        ('black_win', 'Vitória Pretas'),
        ('draw', 'Empate'),
        ('forfeit_white', 'WO Brancas'),
        ('forfeit_black', 'WO Pretas'),
        ('bye', 'Bye'),
    ]

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    white_player = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='white_matches')
    black_player = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='black_matches', null=True, blank=True)  # Allow null for byes
    round_number = models.IntegerField()
    result = models.CharField(max_length=15, choices=RESULT_CHOICES, default='pending')
    board_number = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['round_number', 'board_number']
        unique_together = [
            ('tournament', 'white_player', 'black_player', 'round_number'),
            ('tournament', 'round_number', 'white_player'),
            ('tournament', 'round_number', 'black_player'),
        ]
        verbose_name = "Partida"
        verbose_name_plural = "Partidas"

    def __str__(self):
        if self.black_player:
            return f"Round {self.round_number}: {self.white_player.get_display_name()} vs {self.black_player.get_display_name()}"
        return f"Round {self.round_number}: {self.white_player.get_display_name()} (Bye)"

    def save(self, *args, **kwargs):
        if self.result != 'pending':
            self._update_scores()
        super().save(*args, **kwargs)

    def _update_scores(self):
        if self.result == 'white_win':
            self.white_player.score += 1
        elif self.result == 'black_win':
            self.black_player.score += 1
        elif self.result == 'draw':
            self.white_player.score += 0.5
            self.black_player.score += 0.5
        elif self.result == 'forfeit_white':
            self.black_player.score += 1
        elif self.result == 'forfeit_black':
            self.white_player.score += 1
        elif self.result == 'bye':
            self.white_player.score += 1
        
        self.white_player.save()
        if self.black_player:
            self.black_player.save()