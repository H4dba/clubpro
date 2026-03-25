from django.db import models
from django.contrib.auth.models import AbstractUser



class TiposPlano(models.Model):
    """Modelo para definir diferentes tipos de planos de assinatura do clube"""
    nome = models.CharField(max_length=120, unique=True, verbose_name="Nome do Plano")
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Preço")
    duracao = models.IntegerField(default=30, verbose_name="Duração (dias)")

    class Meta:
        verbose_name = "Tipo de Plano"
        verbose_name_plural = "Tipos de Planos"

    def __str__(self):
        return self.nome


class UsuarioCustom(AbstractUser):
    """Modelo customizado de usuário com informações específicas do clube"""
    tipo_plano = models.ForeignKey(
        TiposPlano, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Tipo de Plano"
    )

    data_nascimento = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="usuario_custom_set",
        blank=True,
        verbose_name="Grupos"
    )
    
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="usuario_custom_permissions_set",
        blank=True,
        verbose_name="Permissões"
    )

    chesscom_username = models.CharField(max_length=100, null=True, blank=True, verbose_name="Usuário Chess.com")
    is_chesscom_connected = models.BooleanField(default=False, verbose_name="Conectado ao Chess.com")

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def verifica_membro_pago(self):
        """Verifica se o usuário possui um plano pago"""
        return self.tipo_plano and self.tipo_plano.preco > 0

    @property
    def perfil_chesscom(self):
        """Retorna o perfil do Chess.com associado ao usuário"""
        try:
            return self.chesscomprofile
        except ChessComProfile.DoesNotExist:
            return None

    def __str__(self):
        return f"{self.username} - {self.first_name} {self.last_name}".strip()


class ChessComProfile(models.Model):
    """Perfil completo do usuário no Chess.com com estatísticas detalhadas"""
    user = models.OneToOneField(UsuarioCustom, on_delete=models.CASCADE, verbose_name="Usuário")
    chesscom_username = models.CharField(max_length=100, unique=True, verbose_name="Usuário Chess.com")
    
    # Ratings e jogos por controle de tempo
    bullet_rating = models.IntegerField(null=True, blank=True, verbose_name="Rating Bullet")
    bullet_games_played = models.IntegerField(null=True, blank=True, verbose_name="Jogos Bullet")
    blitz_rating = models.IntegerField(null=True, blank=True, verbose_name="Rating Blitz")
    blitz_games_played = models.IntegerField(null=True, blank=True, verbose_name="Jogos Blitz")
    rapid_rating = models.IntegerField(null=True, blank=True, verbose_name="Rating Rapid")
    rapid_games_played = models.IntegerField(null=True, blank=True, verbose_name="Jogos Rapid")
    daily_rating = models.IntegerField(null=True, blank=True, verbose_name="Rating Daily")
    daily_games_played = models.IntegerField(null=True, blank=True, verbose_name="Jogos Daily")
    
    # Puzzles / Tactics
    tactics_highest = models.IntegerField(null=True, blank=True, verbose_name="Tactics (maior rating)")
    puzzle_rush_best = models.IntegerField(null=True, blank=True, verbose_name="Puzzle Rush (melhor score)")
    
    # FIDE (retornado pela API do Chess.com)
    fide_rating = models.IntegerField(null=True, blank=True, verbose_name="Rating FIDE")
    
    profile_url = models.URLField(null=True, blank=True, verbose_name="URL do Perfil")

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_at_local = models.DateTimeField(auto_now_add=True, verbose_name="Criado em (local)")

    class Meta:
        verbose_name = "Perfil do Chess.com"
        verbose_name_plural = "Perfis do Chess.com"

    def __str__(self):
        return f"Perfil Chess.com de {self.user.username}"

    def atualizar_de_api(self, dados_api):
        """Atualiza o perfil com dados da API do Chess.com (/pub/player/{username}/stats)"""
        for tc, field_prefix in [('chess_bullet', 'bullet'), ('chess_blitz', 'blitz'),
                                  ('chess_rapid', 'rapid'), ('chess_daily', 'daily')]:
            tc_data = dados_api.get(tc, {})
            last = tc_data.get('last', {})
            record = tc_data.get('record', {})
            setattr(self, f'{field_prefix}_rating', last.get('rating'))
            total = (record.get('win', 0) + record.get('loss', 0) + record.get('draw', 0)) or None
            setattr(self, f'{field_prefix}_games_played', total)

        tactics = dados_api.get('tactics', {})
        self.tactics_highest = tactics.get('highest', {}).get('rating')

        pr = dados_api.get('puzzle_rush', {})
        self.puzzle_rush_best = pr.get('best', {}).get('score')

        self.fide_rating = dados_api.get('fide') or None

        self.profile_url = f'https://www.chess.com/member/{self.chesscom_username}'
        self.save()

    @property
    def maior_rating(self):
        ratings = [r for r in [self.bullet_rating, self.blitz_rating,
                               self.rapid_rating, self.daily_rating] if r]
        return max(ratings) if ratings else None

    @property
    def total_jogos(self):
        jogos = [g for g in [self.bullet_games_played, self.blitz_games_played,
                             self.rapid_games_played, self.daily_games_played] if g]
        return sum(jogos) if jogos else 0

    @property
    def categoria_principal(self):
        categorias = {
            'bullet': self.bullet_games_played or 0,
            'blitz': self.blitz_games_played or 0,
            'rapid': self.rapid_games_played or 0,
            'daily': self.daily_games_played or 0,
        }
        return max(categorias, key=categorias.get) if any(categorias.values()) else None
