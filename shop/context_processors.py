from django.conf import settings


def shop_visibility(request):
    """
    Exposes whether shop links should be shown to the current user.

    Mirrors the gate in ``ShopGateMiddleware``: the shop is visible when it is
    enabled for everyone (``SHOP_ENABLED``) or the user is a superuser.
    """
    user = getattr(request, 'user', None)
    visible = settings.SHOP_ENABLED or bool(
        user and user.is_authenticated and user.is_superuser
    )
    return {'shop_visible': visible}
