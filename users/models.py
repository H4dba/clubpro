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

    def verifica_membro_pago(self):
        return self.tipo_plano and self.tipo_plano.preco > 0

    
