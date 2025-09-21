from django.db import models
from django.conf import settings

class Tournament(models.Model):
    """Modelo para representar torneios de xadrez"""
    
    TOURNAMENT_TYPES = [
        ('arena', 'Arena'),
        ('swiss', 'Suíço'),
    ]
    
    TOURNAMENT_SPEEDS = [
        ('ultraBullet', 'Ultra Bullet'),
        ('bullet', 'Bullet'),
        ('blitz', 'Blitz'),
        ('rapid', 'Rápido'),
        ('classical', 'Clássico'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('created', 'Criado no Lichess'),
        ('started', 'Iniciado'),
        ('finished', 'Finalizado'),
        ('cancelled', 'Cancelado'),
    ]

    name = models.CharField(max_length=100, verbose_name="Nome do Torneio")
    description = models.TextField(blank=True, verbose_name="Descrição")
    tournament_type = models.CharField(
        max_length=10, 
        choices=TOURNAMENT_TYPES, 
        verbose_name="Tipo de Torneio"
    )
    clock_limit = models.IntegerField(
        verbose_name="Tempo Inicial",
        help_text="Tempo inicial em minutos"
    )
    clock_increment = models.IntegerField(
        verbose_name="Incremento", 
        help_text="Incremento em segundos"
    )
    minutes = models.IntegerField(
        verbose_name="Duração",
        help_text="Duração do torneio em minutos"
    )
    tournament_speed = models.CharField(
        max_length=20, 
        choices=TOURNAMENT_SPEEDS,
        verbose_name="Velocidade do Torneio"
    )
    start_time = models.DateTimeField(verbose_name="Hora de Início")
    lichess_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="ID do Lichess"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="Criado por"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    is_private = models.BooleanField(default=False, verbose_name="Torneio Privado")
    min_rating = models.IntegerField(
        null=True, 
        blank=True,
        verbose_name="Rating Mínimo"
    )
    max_rating = models.IntegerField(
        null=True, 
        blank=True,
        verbose_name="Rating Máximo"
    )
    password = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Senha"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Status"
    )

    class Meta:
        ordering = ['-start_time']
        verbose_name = "Torneio"
        verbose_name_plural = "Torneios"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Retorna a URL absoluta do torneio"""
        from django.urls import reverse
        return reverse('main:tournament_detail', args=[str(self.id)])

    @property
    def is_finished(self):
        """Verifica se o torneio já terminou"""
        return self.status == 'finished'

    @property
    def is_active(self):
        """Verifica se o torneio está ativo (iniciado mas não finalizado)"""
        return self.status == 'started'