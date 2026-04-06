"""Unit tests for librarian SQL parsing helpers."""

from apps.api.services.librarian_service import LibrarianService


def _build_service_for_parse_tests() -> LibrarianService:
    service = LibrarianService.__new__(LibrarianService)
    service.platform_spec = {"qa_rules": {"data_type_mapping": {}}}
    return service


def test_parse_create_table_statements_recovers_mysql_tables_from_mixed_script():
    service = _build_service_for_parse_tests()

    ddl_content = """
    CREATE TABLE IF NOT EXISTS dim_cliente (
        cliente_key INT NOT NULL AUTO_INCREMENT,
        nombre VARCHAR(200),
        PRIMARY KEY (cliente_key)
    );

    DELIMITER $$
    CREATE PROCEDURE sp_test()
    BEGIN
        SELECT CONCAT('ok -- ins: ', 1) AS resultado;
    END$$
    DELIMITER ;

    CREATE TABLE IF NOT EXISTS fact_ventas (
        venta_key INT NOT NULL AUTO_INCREMENT,
        fecha_venta DATE,
        PRIMARY KEY (venta_key)
    );
    """

    recovered = service._parse_create_table_statements(ddl_content, dialect="mysql")

    assert "dim_cliente" in recovered
    assert "fact_ventas" in recovered
    assert len(recovered) == 2


def test_parse_ddl_mysql_fallback_recovers_tables_when_full_parse_fails():
    service = _build_service_for_parse_tests()

    ddl_content = """
    CREATE TABLE IF NOT EXISTS dim_fecha (
        fecha_key INT NOT NULL AUTO_INCREMENT,
        fecha DATE,
        PRIMARY KEY (fecha_key)
    );

    CREATE PROCEDURE sp_bad_block()
    BEGIN
        IF NOT EXISTS (
            SELECT 1
        ) THEN
            CALL sp_demo();
        ELSE
            SELECT 'skip' AS log_orquestador;
        END IF;
    END;
    """

    tables = service._parse_ddl(ddl_content, dialect="mysql")

    assert "dim_fecha" in tables
