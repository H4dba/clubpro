from django import template
from socios.models import Socio

register = template.Library()


@register.simple_tag
def get_socio_for_user(user):
    """Retorna o Socio vinculado ao usuário, ou None se não for sócio."""
    if not getattr(user, 'is_authenticated', False):
        return None
    try:
        return Socio.objects.get(usuario=user)
    except Socio.DoesNotExist:
        return None
