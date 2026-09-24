from django.conf import settings
from django.shortcuts import redirect


class ShopGateMiddleware:
    """
    Restricts the shop to superusers while it is being validated in production.

    When ``settings.SHOP_ENABLED`` is False, any request under the ``/shop/``
    prefix from a non-superuser is redirected to the "em breve" page. Set
    ``SHOP_ENABLED=True`` in the environment to open the shop to everyone.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/shop/'):
            user = getattr(request, 'user', None)
            shop_open = settings.SHOP_ENABLED or bool(
                user and user.is_authenticated and user.is_superuser
            )
            if not shop_open:
                return redirect('em_breve')
        return self.get_response(request)
