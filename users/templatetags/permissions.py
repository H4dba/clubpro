from django import template

register = template.Library()

@register.simple_tag
def can_see_socios_dropdown(user):
    print('Estou aqui')
    """Verifica se o usuário é admin ou tem permissões de gestão"""
    
    if not getattr(user, 'is_authenticated', False):
        return False

    # Superuser ou staff têm acesso
    if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
        return True

    # Grupos comuns de gestão (ajuste nomes conforme sua aplicação)
    manager_groups = [
        'admin',
        'management'
    ]
    if user.groups.filter(name__in=manager_groups).exists():
        return True

    # Permissões específicas que indiquem capacidade de gerenciar sócios
    gerente_perms = [
        'socios.add_socio',
        'socios.change_socio',
        'socios.delete_socio',
        'socios.manage_socios',
    ]
    for perm in gerente_perms:
        if user.has_perm(perm):
            return True

    return False