"""
AbacatePay integration service for shop order payments.
"""
from __future__ import annotations

import logging
from abacatepay.billings.models import Billing
from abacatepay.constants import BASE_URL, USER_AGENT
from django.conf import settings
from socios.services import _api_key, _post_billing, sanitize_abacatepay_url

logger = logging.getLogger(__name__)


def criar_cobranca_pedido(
    *,
    order,
    return_url: str,
    completion_url: str,
) -> dict:
    """
    Cria uma cobrança no AbacatePay para os itens do pedido da loja.

    Returns a dict with keys: billing_id, billing_url, valor_cents.
    """
    return_url = sanitize_abacatepay_url(return_url)
    completion_url = sanitize_abacatepay_url(completion_url)
    products_payload = []
    for item in order.items.all():
        # Valor em centavos
        valor_cents = int(item.price * 100)
        products_payload.append({
            "externalId": f"produto-{item.product.id}",
            "name": item.product.name,
            "quantity": item.quantity,
            "price": valor_cents,
            "description": item.product.short_description or item.product.name,
        })

    payload = {
        "frequency": "ONE_TIME",
        "methods": ["PIX"],
        "products": products_payload,
        "returnUrl": return_url,
        "completionUrl": completion_url,
        "customer": {
            "name": order.customer_name or "Cliente",
            "email": order.customer_email,
            "taxId": order.customer_cpf or "",
            "cellphone": order.customer_phone or "(00) 00000-0000",
        },
    }

    billing = _post_billing(_api_key(), payload)

    return {
        "billing_id": billing.id,
        "billing_url": billing.url,
        "valor_cents": int(order.total * 100),
    }
