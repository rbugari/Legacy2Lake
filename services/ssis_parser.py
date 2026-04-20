from apps.utm.cartridges.ssis.parser import _LegacySSISLogic


class SSISParser:
    """Backward-compatible SSIS parser facade for legacy imports/tests."""

    def __init__(self, content: str):
        namespaces = {
            "DTS": "www.microsoft.com/SqlServer/Dts",
            "SQLTask": "www.microsoft.com/sqlserver/dts/tasks/sqltask",
        }
        self._parser = _LegacySSISLogic(content, namespaces)

    def get_summary(self):
        return self._parser.get_summary()

    def extract_executables(self):
        return self._parser.extract_executables()

    def extract_precedence_constraints(self):
        return self._parser.extract_precedence_constraints()

    def get_data_flow_components(self):
        return self._parser.get_data_flow_components()

    def get_logical_medulla(self):
        return self._parser.get_logical_medulla()