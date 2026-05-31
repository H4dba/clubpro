"""
AbacatePay integration service for membership payments.
"""
from __future__ import annotations

import logging

import requests
from abacatepay.billings.models import Billing
from abacatepay.constants import BASE_URL, USER_AGENT
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
    if key.startswith("webh_"):
        raise ValueError(
            "ABACATEPAY_API_KEY parece ser um webhook secret (prefixo 'webh_'). "
            "Use a API key gerada no painel do AbacatePay, não o secret do webhook."
        )
    return key


def _base_url() -> str:
    """Base da API AbacatePay (configurável via ABACATEPAY_API_BASE_URL)."""
    return (settings.ABACATEPAY_API_BASE_URL or BASE_URL).rstrip("/")


def _post_billing(api_key: str, payload: dict) -> Billing:
    """
    Low-level POST to /billing/create.

    We bypass the SDK's prepare_data() because it serialises customer_id=None
    as  {"customerId": null}  which the AbacatePay API rejects with a 422.
    Using model_dump(exclude_none=True) keeps the body clean.
    """
    response = requests.post(
        f"{_base_url()}/billing/create",
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


def sanitize_abacatepay_url(url: str) -> str:
    """
    AbacatePay SDK validates return_url and completion_url using a regex:
    ^(https?:\/\/)(([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})(\/[^\s]*)?$
    This regex fails for local hosts like 'localhost' or raw IPs like '127.0.0.1'.
    We dynamically rewrite local addresses to use '127.0.0.1.nip.io' (wildcard DNS)
    so they pass validation and resolve correctly to the local machine.
    """
    from urllib.parse import urlparse, urlunparse
    parsed = urlparse(url)
    netloc = parsed.netloc
    
    # Extract host and port
    if ":" in netloc:
        host, port = netloc.split(":", 1)
        port_suffix = f":{port}"
    else:
        host = netloc
        port_suffix = ""
        
    # Check if host is local (localhost or raw IP)
    is_ip = all(c.isdigit() or c == '.' for c in host)
    if host.lower() == 'localhost' or is_ip:
        new_host = "127.0.0.1.nip.io"
        new_netloc = f"{new_host}{port_suffix}"
        parsed = parsed._replace(netloc=new_netloc)
        
    return urlunparse(parsed)


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
    return_url = sanitize_abacatepay_url(return_url)
    completion_url = sanitize_abacatepay_url(completion_url)
    valor_cents = int(tipo_assinatura.valor_mensal * 100)

    payload = {
        "frequency": "ONE_TIME",
        "methods": ["PIX"],
        "products": [
            {
                "externalId": f"plano-{tipo_assinatura.id}",
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
        "returnUrl": return_url,
        "completionUrl": completion_url,
        "customer": {
            "name": socio_nome or "Sócio",
            "email": socio_email,
            "taxId": socio_cpf,
            "cellphone": socio_telefone or "(00) 00000-0000",
        },
    }

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
        f"{_base_url()}/billing/list",
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
