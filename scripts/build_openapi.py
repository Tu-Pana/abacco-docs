"""Genera api-reference/openapi.json (API /v1, Api-Key) para docs.abacco.ai.

Reusa los paths compartidos del spec combinado de docs.tupana.ai (mismo
backend) y agrega la API publica de remuneraciones. El spec de contabilidad
(/api/accounting, Bearer) vive aparte en openapi-accounting.json.
"""

import json
import os

TUPANA_SPEC = os.path.expanduser(
    "~/dev/tupana/docs/api-reference/openapi-combined.json"
)
SHARED_PATHS = [
    "/documents",
    "/documents/batch",
    "/documents/{document_id}",
    "/master-entities",
    "/book-summaries",
]

ID_PARAM = {
    "name": "id",
    "in": "path",
    "required": True,
    "schema": {"type": "string"},
    "description": "Id opaco (eid_...) o entero",
}
ENTITY_PARAM = {
    "name": "master_entity_id",
    "in": "query",
    "required": True,
    "schema": {"type": "string"},
    "description": "Id opaco (eid_...) o entero de la empresa",
}
PAGE_PARAMS = [
    {"name": "page", "in": "query", "schema": {"type": "integer"}},
    {"name": "page_size", "in": "query", "schema": {"type": "integer"}},
]

EMPLOYEE = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "example": "eid_AbC123"},
        "rut": {"type": "string", "example": "12.345.678-9"},
        "full_name": {"type": "string"},
        "is_active": {"type": "boolean"},
        "worker_type": {"type": "string"},
        "contract_type": {"type": "string"},
        "base_salary": {"type": "number"},
        "start_date": {"type": "string", "format": "date"},
        "position": {"type": "string"},
        "afp": {"type": "string"},
        "health_system": {"type": "string"},
    },
}
PAYSLIP = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "employee_rut": {"type": "string"},
        "employee_name": {"type": "string"},
        "worked_days": {"type": "number"},
        "total_earnings": {"type": "number"},
        "total_taxable": {"type": "number"},
        "total_deductions": {"type": "number"},
        "net_pay": {"type": "number"},
        "employer_cost": {"type": "number"},
        "availability": {"type": "string"},
    },
}
PAYSLIP_DETAIL = {
    "allOf": [
        {"$ref": "#/components/schemas/PayrollPayslip"},
        {
            "type": "object",
            "properties": {
                "lines": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "name": {"type": "string"},
                            "kind": {"type": "string"},
                            "amount": {"type": "number"},
                        },
                    },
                }
            },
        },
    ]
}
RUN = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "period": {"type": "string", "example": "202607"},
        "status": {"type": "string"},
        "closed_at": {"type": "string", "format": "date-time", "nullable": True},
        "paid_at": {"type": "string", "format": "date-time", "nullable": True},
        "totals": {"type": "object", "additionalProperties": True},
    },
}


def _list_response(item_ref):
    return {
        "200": {
            "description": "OK",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "count": {"type": "integer"},
                            "results": {"type": "array", "items": item_ref},
                        },
                    }
                }
            },
        }
    }


def _detail_response(item_ref):
    return {
        "200": {
            "description": "OK",
            "content": {"application/json": {"schema": item_ref}},
        }
    }


def payroll_paths():
    emp = {"$ref": "#/components/schemas/PayrollEmployee"}
    slip = {"$ref": "#/components/schemas/PayrollPayslip"}
    slip_detail = {"$ref": "#/components/schemas/PayrollPayslipDetail"}
    run = {"$ref": "#/components/schemas/PayrollRun"}
    period = {
        "name": "period",
        "in": "query",
        "schema": {"type": "string"},
        "description": "Periodo YYYYMM (ej. 202607)",
    }
    return {
        "/payroll/employees/": {
            "get": {
                "operationId": "listPayrollEmployees",
                "summary": "Listar empleados",
                "tags": ["Remuneraciones"],
                "parameters": [ENTITY_PARAM] + PAGE_PARAMS,
                "responses": _list_response(emp),
            }
        },
        "/payroll/employees/{id}/": {
            "get": {
                "operationId": "getPayrollEmployee",
                "summary": "Detalle de un empleado",
                "tags": ["Remuneraciones"],
                "parameters": [ID_PARAM],
                "responses": _detail_response(emp),
            }
        },
        "/payroll/runs/": {
            "get": {
                "operationId": "listPayrollRuns",
                "summary": "Listar procesos de nomina",
                "tags": ["Remuneraciones"],
                "parameters": [ENTITY_PARAM, period],
                "responses": _list_response(run),
            }
        },
        "/payroll/runs/{id}/": {
            "get": {
                "operationId": "getPayrollRun",
                "summary": "Detalle de un proceso",
                "tags": ["Remuneraciones"],
                "parameters": [ID_PARAM],
                "responses": _detail_response(run),
            }
        },
        "/payroll/runs/{id}/payslips/": {
            "get": {
                "operationId": "listPayrollRunPayslips",
                "summary": "Liquidaciones de un proceso",
                "tags": ["Remuneraciones"],
                "parameters": [ID_PARAM],
                "responses": _list_response(slip),
            }
        },
        "/payroll/payslips/{id}/": {
            "get": {
                "operationId": "getPayslip",
                "summary": "Detalle de una liquidacion (con lineas)",
                "tags": ["Remuneraciones"],
                "parameters": [ID_PARAM],
                "responses": _detail_response(slip_detail),
            }
        },
        "/payroll/indicators/": {
            "get": {
                "operationId": "getPayrollIndicators",
                "summary": "Indicadores previsionales del periodo",
                "tags": ["Remuneraciones"],
                "parameters": [
                    {
                        "name": "period",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Periodo YYYYMM",
                    }
                ],
                "responses": _detail_response(
                    {"type": "object", "additionalProperties": True}
                ),
            }
        },
    }


def main():
    src = json.load(open(TUPANA_SPEC))
    spec = {
        "openapi": src.get("openapi", "3.0.3"),
        "info": {
            "title": "API de Abacco",
            "version": "1.0.0",
            "description": "API publica de Abacco (Api-Key).",
        },
        "servers": [
            {"url": "https://api.abacco.ai/v1", "description": "Produccion"}
        ],
        "security": src.get("security", [{"apiKeyAuth": []}]),
        "paths": {p: src["paths"][p] for p in SHARED_PATHS if p in src["paths"]},
        "components": src.get("components", {}),
    }
    spec["paths"].update(payroll_paths())
    schemas = spec["components"].setdefault("schemas", {})
    schemas["PayrollEmployee"] = EMPLOYEE
    schemas["PayrollPayslip"] = PAYSLIP
    schemas["PayrollPayslipDetail"] = PAYSLIP_DETAIL
    schemas["PayrollRun"] = RUN
    out = os.path.join(os.path.dirname(__file__), "..", "api-reference", "openapi.json")
    json.dump(spec, open(out, "w"), ensure_ascii=False, indent=1)
    print("written", out, "paths:", len(spec["paths"]))


if __name__ == "__main__":
    main()
