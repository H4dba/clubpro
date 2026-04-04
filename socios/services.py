"""
AbacatePay integration service for membership payments.
"""
from __future__ import annotations

import logging

import requests
from abacatepay.billings.models import Billing, BillingIn
from abacatepay.constants import BASE_URL, USER_AGENT
from abacatepay.customers.models import CustomerMetadata
from abacatepay.utils.exceptions import raise_for_status
from django.conf import settings

logger = logging.getLogger(__name__)


def _api_key() -> str:
    key = settings.ABACATEPAY_API_KEY
    if not key:
        raise ValueError(
            "ABACATEPAY_API_KEY não configurada. "
            "Adicione a chave no arquivo .env para habilitar pagamentos."
        )
    return key


def _post_billing(api_key: str, payload: dict) -> Billing:
    """
    Low-level POST to /billing/create.

    We bypass the SDK's prepare_data() because it serialises customer_id=None
    as  {"customerId": null}  which the AbacatePay API rejects with a 422.
    Using model_dump(exclude_none=True) keeps the body clean.
    """
    response = requests.post(
        f"{BASE_URL}/billing/create",
        json=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
        },
        timeout=30,
    )

    if not response.ok:
        logger.error(
            "AbacatePay billing create failed – status %s – body: %s",
            response.status_code,
            response.text,
        )

    raise_for_status(response)
    return Billing(**response.json()["data"])


def criar_cobranca_associacao(
    *,
    tipo_assinatura,
    socio_nome: str,
    socio_email: str,
    socio_cpf: str,
    socio_telefone: str,
    return_url: str,
    completion_url: str,
) -> dict:
    """
    Cria uma cobrança no AbacatePay para o plano de associação informado.

    Returns a dict with keys: billing_id, billing_url, valor_cents.
    """
    valor_cents = int(tipo_assinatura.valor_mensal * 100)

    billing_in = BillingIn(
        products=[
            {
                "external_id": f"plano-{tipo_assinatura.id}",
                "name": tipo_assinatura.nome,
                "quantity": 1,
                "price": valor_cents,
                "description": (
                    tipo_assinatura.descricao.strip()
                    if tipo_assinatura.descricao
                    else f"Assinatura {tipo_assinatura.nome}"
                ),
            }
        ],
        return_url=return_url,
        completion_url=completion_url,
        customer=CustomerMetadata(
            name=socio_nome or "Sócio",
            email=socio_email,
            tax_id=socio_cpf,
            cellphone=socio_telefone or "(00) 00000-0000",
        ),
    )

    # exclude_none=True ensures customerId (and any other None field) is never
    # sent in the request body, which the AbacatePay API rejects with a 422.
    payload = billing_in.model_dump(by_alias=True, exclude_none=True)

    billing = _post_billing(_api_key(), payload)

    return {
        "billing_id": billing.id,
        "billing_url": billing.url,
        "valor_cents": valor_cents,
    }


def verificar_status_cobranca(billing_id: str) -> str | None:
    """
    Fetches the billing list from AbacatePay and returns the status string
    (e.g. 'PAID', 'PENDING') of the billing with the given ID, or None if
    not found.
    """
    api_key = _api_key()

    response = requests.get(
        f"{BASE_URL}/billing/list",
        headers={
            "Authorization": f"Bearer {api_key}",
            "User-Agent": USER_AGENT,
        },
        timeout=15,
    )

    if not response.ok:
        logger.error(
            "AbacatePay billing list failed – status %s – body: %s",
            response.status_code,
            response.text,
        )
        raise_for_status(response)

    billings = response.json().get("data") or []
    for billing in billings:
        if billing.get("id") == billing_id:
            return (billing.get("status") or "").upper()

    return None
