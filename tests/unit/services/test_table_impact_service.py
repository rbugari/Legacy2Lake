"""Unit tests for SQL-first table impact extraction."""

from apps.api.services.table_impact_service import TableImpactService


def _build_service() -> TableImpactService:
    service = TableImpactService.__new__(TableImpactService)
    service.project_id = "project-123"
    service.tenant_id = "tenant-123"
    return service


def test_extract_impacts_from_sql_asset_detects_insert_target_and_select_sources():
    service = _build_service()
    asset = {
        "object_id": "asset-1",
        "source_name": "05_sp_load_fact_ventas.sql",
        "source_tech": "MySQL",
        "raw_content": """
        DELIMITER $$
        CREATE PROCEDURE sp_load_fact_ventas()
        BEGIN
            INSERT INTO fact_ventas (pedido_id_origen, cliente_key)
            SELECT p.id, c.cliente_key
            FROM pedidos p
            JOIN dim_cliente c ON c.cliente_id_origen = p.cliente_id;
        END$$
        """,
    }

    impacts = service._extract_impacts_from_sql_asset(asset)

    assert any(i["full_name"] == "fact_ventas" and i["operation"] == "INSERT" and i["is_target"] for i in impacts)
    assert any(i["full_name"] == "pedidos" and i["operation"] == "SELECT" and i["is_source"] for i in impacts)
    assert any(i["full_name"] == "dim_cliente" and i["operation"] == "SELECT" and i["is_source"] for i in impacts)


def test_extract_impacts_from_sql_asset_detects_update_target_and_join_source():
    service = _build_service()
    asset = {
        "object_id": "asset-2",
        "source_name": "02_sp_load_dim_cliente.sql",
        "source_tech": "MariaDB",
        "raw_content": """
        UPDATE dim_cliente dc
        JOIN clientes c ON c.id = dc.cliente_id_origen
        SET dc.email = c.email,
            dc.telefono = c.telefono
        WHERE dc.es_vigente = 1;
        """,
    }

    impacts = service._extract_impacts_from_sql_asset(asset)

    assert any(i["full_name"] == "dim_cliente" and i["operation"] == "UPDATE" and i["is_target"] for i in impacts)
    assert any(i["full_name"] == "clientes" and i["operation"] == "SELECT" and i["is_source"] for i in impacts)


def test_split_sql_statements_handles_mysql_delimiters_and_procedure_body():
    service = _build_service()

    statements = service._split_sql_statements(
        """
        USE demo_dw;
        DELIMITER $$
        CREATE PROCEDURE sp_demo()
        BEGIN
            INSERT INTO fact_demo SELECT * FROM src_demo;
            UPDATE dim_demo SET es_activo = 1;
        END$$
        DELIMITER ;
        """
    )

    assert any(statement.startswith("INSERT INTO fact_demo") for statement in statements)
    assert any(statement.startswith("UPDATE dim_demo") for statement in statements)


def test_infer_columns_affected_handles_mysql_insert_ignore_without_parser_noise():
    service = _build_service()

    columns = service._infer_columns_affected(
        """
        INSERT IGNORE INTO dim_proveedor (
            proveedor_key,
            proveedor_id_origen,
            nombre_proveedor,
            es_activo
        ) VALUES (-1, -1, 'SIN PROVEEDOR', 0)
        """,
        "INSERT",
    )

    assert columns == [
        "es_activo",
        "nombre_proveedor",
        "proveedor_id_origen",
        "proveedor_key",
    ]
