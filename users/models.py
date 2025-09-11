from django.db import models
from django.contrib.auth.models import AbstractUser



class TiposPlano(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    duracao = models.IntegerField(default=30)

    def __str__(self):
        return self.nome


class UsuarioCustom(AbstractUser):
    tipo_plano = models.ForeignKey(
        TiposPlano, on_delete=models.SET_NULL, null=True, blank=True
    )

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="usuario_custom_set",
        blank=True
    )
    
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="usuario_custom_permissions_set",
        blank=True
    )

<<<<<<< HEAD
=======
    lichess_id = models.CharField(max_length=100, null=True, blank=True)
    lichess_access_token = models.CharField(max_length=255, null=True, blank=True)
    lichess_rating_bullet = models.IntegerField(null=True, blank=True)
    lichess_rating_blitz = models.IntegerField(null=True, blank=True)
    lichess_rating_rapid = models.IntegerField(null=True, blank=True)
    lichess_rating_classical = models.IntegerField(null=True, blank=True)
    is_lichess_connected = models.BooleanField(default=False)

    def update_lichess_ratings(self, ratings_data):
        self.lichess_rating_bullet = ratings_data.get('bullet', {}).get('rating')
        self.lichess_rating_blitz = ratings_data.get('blitz', {}).get('rating')
        self.lichess_rating_rapid = ratings_data.get('rapid', {}).get('rating')
        self.lichess_rating_classical = ratings_data.get('classical', {}).get('rating')
        self.save()

>>>>>>> 6a5248121375816dc7f53a70106fc207186fe823
    def verifica_membro_pago(self):
        return self.tipo_plano and self.tipo_plano.preco > 0

    
