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

    # Campos básicos de integração com Lichess
    lichess_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="ID do Lichess")
    lichess_access_token = models.CharField(max_length=255, null=True, blank=True, verbose_name="Token de Acesso")
    is_lichess_connected = models.BooleanField(default=False, verbose_name="Conectado ao Lichess")

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def verifica_membro_pago(self):
        """Verifica se o usuário possui um plano pago"""
        return self.tipo_plano and self.tipo_plano.preco > 0

    @property
    def perfil_lichess(self):
        """Retorna o perfil do Lichess associado ao usuário"""
        try:
            return self.lichessprofile
        except LichessProfile.DoesNotExist:
            return None

    def __str__(self):
        return f"{self.username} - {self.first_name} {self.last_name}".strip()


class LichessProfile(models.Model):
    """Perfil completo do usuário no Lichess com estatísticas detalhadas"""
    user = models.OneToOneField(UsuarioCustom, on_delete=models.CASCADE, verbose_name="Usuário")
    lichess_id = models.CharField(max_length=100, unique=True, verbose_name="ID do Lichess")
    
    # Estatísticas de jogos por categoria de tempo
    bullet_games_played = models.IntegerField(null=True, blank=True, verbose_name="Jogos Bullet")
    bullet_rating = models.IntegerField(null=True, blank=True, verbose_name="Rating Bullet")
    blitz_games_played = models.IntegerField(null=True, blank=True, verbose_name="Jogos Blitz")
    blitz_rating = models.IntegerField(null=True, blank=True, verbose_name="Rating Blitz")
    rapid_games_played = models.IntegerField(null=True, blank=True, verbose_name="Jogos Rapid")
    rapid_rating = models.IntegerField(null=True, blank=True, verbose_name="Rating Rapid")
    classical_games_played = models.IntegerField(null=True, blank=True, verbose_name="Jogos Classical")
    classical_rating = models.IntegerField(null=True, blank=True, verbose_name="Rating Classical")
    puzzles_solved = models.IntegerField(null=True, blank=True, verbose_name="Problemas Resolvidos")
    puzzles_rating = models.IntegerField(null=True, blank=True, verbose_name="Rating de Problemas")
    
    # Campos adicionais do perfil
    lichess_username = models.CharField(max_length=100, null=True, blank=True, verbose_name="Nome de Usuário")
    country = models.CharField(max_length=10, null=True, blank=True, verbose_name="País")
    title = models.CharField(max_length=10, null=True, blank=True, verbose_name="Título")  # GM, IM, etc.
    patron = models.BooleanField(default=False, verbose_name="Patrono do Lichess")
    created_at = models.DateTimeField(null=True, blank=True, verbose_name="Criado em (Lichess)")
    seen_at = models.DateTimeField(null=True, blank=True, verbose_name="Última vez visto")
    play_time_total = models.IntegerField(null=True, blank=True, verbose_name="Tempo total de jogo (segundos)")
    profile_url = models.URLField(null=True, blank=True, verbose_name="URL do Perfil")
    
    # Controle de datas locais
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_at_local = models.DateTimeField(auto_now_add=True, verbose_name="Criado em (local)")

    class Meta:
        verbose_name = "Perfil do Lichess"
        verbose_name_plural = "Perfis do Lichess"

    def __str__(self):
        return f"Perfil Lichess de {self.user.username}"

    def atualizar_de_api_lichess(self, dados_api):
        """Atualiza o perfil com dados da API do Lichess"""
        perfs = dados_api.get('perfs', {})
        
        # Atualiza ratings e jogos para cada categoria de tempo
        for categoria in ['bullet', 'blitz', 'rapid', 'classical']:
            if categoria in perfs:
                perf_data = perfs[categoria]
                setattr(self, f'{categoria}_rating', perf_data.get('rating'))
                setattr(self, f'{categoria}_games_played', perf_data.get('games'))
        
        # Atualiza dados de problemas
        if 'puzzle' in perfs:
            puzzle_data = perfs['puzzle']
            self.puzzles_rating = puzzle_data.get('rating')
            self.puzzles_solved = puzzle_data.get('games')
        
        # Atualiza outros campos do perfil
        self.lichess_username = dados_api.get('username')
        self.country = dados_api.get('profile', {}).get('country')
        self.title = dados_api.get('title')
        self.patron = dados_api.get('patron', False)
        
        # Converte timestamps se existirem
        if 'createdAt' in dados_api:
            from datetime import datetime
            self.created_at = datetime.fromtimestamp(dados_api['createdAt'] / 1000)
        if 'seenAt' in dados_api:
            from datetime import datetime
            self.seen_at = datetime.fromtimestamp(dados_api['seenAt'] / 1000)
        
        self.save()

    @property
    def maior_rating(self):
        """Retorna o maior rating entre todas as categorias"""
        ratings = [r for r in [self.bullet_rating, self.blitz_rating, 
                              self.rapid_rating, self.classical_rating] if r]
        return max(ratings) if ratings else None

    @property
    def total_jogos(self):
        """Retorna o total de jogos em todas as categorias"""
        jogos = [g for g in [self.bullet_games_played, self.blitz_games_played,
                            self.rapid_games_played, self.classical_games_played] if g]
        return sum(jogos) if jogos else 0

    @property
    def categoria_principal(self):
        """Retorna a categoria com mais jogos"""
        categorias = {
            'bullet': self.bullet_games_played or 0,
            'blitz': self.blitz_games_played or 0,
            'rapid': self.rapid_games_played or 0,
            'classical': self.classical_games_played or 0,
        }
        return max(categorias, key=categorias.get) if any(categorias.values()) else None


