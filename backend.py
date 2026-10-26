import re
import secrets
from typing import Any

DEVEDORES: dict[str, dict[str, Any]] = {
    "11111111111": {
        "nome": "João da Silva",
        "data_nascimento": "01/01/1990",
        "dividas": [
            {
                "id": "DIV-1001",
                "credor": "Loja Exemplo",
                "valor": 1234.56,
                "vencimento": "10/01/2026",
            },
            {
                "id": "DIV-1002",
                "credor": "Cartão Exemplo",
                "valor": 350.00,
                "vencimento": "05/02/2026",
            },
        ],
    },
    "22222222222": {
        "nome": "Maria Souza",
        "data_nascimento": "02/02/1985",
        "dividas": [
            {
                "id": "DIV-2001",
                "credor": "Banco Exemplo",
                "valor": 4890.00,
                "vencimento": "15/11/2025",
            },
        ],
    },
    "33333333333": {
        "nome": "Carlos Pereira",
        "data_nascimento": "03/03/2000",
        "dividas": [],
    },
}

PLANOS: dict[str, dict[str, Any]] = {
    "a_vista": {
        "descricao": "À vista com 10% de desconto",
        "parcelas": 1,
        "juros_mensal": 0.0,
        "desconto": 0.10,
    },
    "3x": {
        "descricao": "3 parcelas sem juros",
        "parcelas": 3,
        "juros_mensal": 0.0,
        "desconto": 0.0,
    },
    "6x": {
        "descricao": "6 parcelas com juros de 1,99% ao mês",
        "parcelas": 6,
        "juros_mensal": 0.0199,
        "desconto": 0.0,
    },
    "12x": {
        "descricao": "12 parcelas com juros de 2,49% ao mês",
        "parcelas": 12,
        "juros_mensal": 0.0249,
        "desconto": 0.0,
    },
}

ACORDOS: dict[str, dict[str, Any]] = {}


def _somente_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def _normalizar_data(valor: str) -> str:
    valor = (valor or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor):
        ano, mes, dia = valor.split("-")
        return f"{dia}/{mes}/{ano}"

    digitos = _somente_digitos(valor)
    if len(digitos) == 8:
        return f"{digitos[:2]}/{digitos[2:4]}/{digitos[4:]}"

    return valor


def _buscar_devedor(cpf: str) -> dict[str, Any] | None:
    return DEVEDORES.get(_somente_digitos(cpf))


def _valor_total(devedor: dict[str, Any]) -> float:
    return round(sum(divida["valor"] for divida in devedor["dividas"]), 2)


def _calcular_plano(valor_total: float, plano_id: str) -> dict[str, Any]:
    plano = PLANOS[plano_id]
    base = valor_total * (1 - plano["desconto"])
    total = base * ((1 + plano["juros_mensal"]) ** plano["parcelas"])
    parcela = round(total / plano["parcelas"], 2)
    total = round(parcela * plano["parcelas"], 2)
    return {
        "plano_id": plano_id,
        "descricao": plano["descricao"],
        "parcelas": plano["parcelas"],
        "valor_parcela": parcela,
        "valor_total": total,
    }


async def consultar_divida(cpf: str, data_nascimento: str) -> dict[str, Any]:
    devedor = _buscar_devedor(cpf)
    if not devedor:
        return {"encontrado": False, "mensagem": "Não localizei esse CPF na base."}

    if _normalizar_data(data_nascimento) != devedor["data_nascimento"]:
        return {"encontrado": False, "mensagem": "Os dados informados não conferem."}

    if not devedor["dividas"]:
        return {
            "encontrado": True,
            "nome": devedor["nome"],
            "tem_divida": False,
            "mensagem": "Não há dívidas em aberto para este CPF.",
        }

    return {
        "encontrado": True,
        "nome": devedor["nome"],
        "tem_divida": True,
        "valor_total": _valor_total(devedor),
        "dividas": devedor["dividas"],
    }


async def listar_planos(cpf: str) -> dict[str, Any]:
    devedor = _buscar_devedor(cpf)
    if not devedor or not devedor["dividas"]:
        return {"erro": "Não há dívida em aberto para este CPF."}

    total = _valor_total(devedor)
    return {
        "valor_total": total,
        "planos": [_calcular_plano(total, plano_id) for plano_id in PLANOS],
    }


async def criar_acordo(cpf: str, plano_id: str) -> dict[str, Any]:
    devedor = _buscar_devedor(cpf)
    if not devedor or not devedor["dividas"]:
        return {"erro": "Não há dívida em aberto para este CPF."}

    if plano_id not in PLANOS:
        return {"erro": f"Plano inválido: {plano_id}."}

    plano = _calcular_plano(_valor_total(devedor), plano_id)
    acordo_id = f"ACR-{secrets.token_hex(3).upper()}"
    acordo = {
        "acordo_id": acordo_id,
        "cpf": _somente_digitos(cpf),
        "nome": devedor["nome"],
        **plano,
        "link_pagamento": f"https://pagamento.exemplo/{acordo_id}",
    }
    ACORDOS[acordo_id] = acordo
    return acordo


async def transferir_para_humano(motivo: str) -> dict[str, Any]:
    return {
        "status": "transferido",
        "protocolo": f"ATD-{secrets.token_hex(3).upper()}",
        "motivo": motivo,
    }
