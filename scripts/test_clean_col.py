import re

def clean_col(raw):
    if not raw:
        return ''
    m = re.search(r'Columns\[([^\]]+)\]', raw, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    token = raw.split('::')[-1]
    token = token.split('.')[-1]
    token = token.strip().strip('[]"')
    return token

def infer_col_type(col_name):
    lower = col_name.lower()
    if any(k in lower for k in ('date', 'time', 'timestamp', 'created', 'updated', 'modified', 'fecha', 'hora')):
        return 'DATE'
    if any(k in lower for k in ('amount', 'price', 'cost', 'rate', 'salary', 'total', 'subtotal', 'tax', 'discount', 'valor', 'importe')):
        return 'DECIMAL'
    if any(k in lower for k in ('flag', 'active', 'enabled', 'deleted', 'is_', 'has_')) or lower.startswith(('is', 'has', 'can', 'allow')):
        return 'BOOLEAN'
    if any(k in lower for k in ('id', 'key', 'num', 'count', 'qty', 'quantity', 'age', 'year', 'month', 'day', 'code', 'seq', 'order')):
        return 'INTEGER'
    return 'VARCHAR'

samples = [
    r'Package\DimCustomer\OLE DB Destination.Inputs[OLE DB Destination Input].ExternalColumns[custid]',
    r'Package\DimCategory\OLE DB Source.Outputs[OLE DB Source Output].ExternalColumns[categoryid]',
    r'Package\FactSales\Derived Column.Outputs[Derived Column Output].Columns[SaleDate]',
    'simple_col_name',
    r'Package\DimDate\Source.ExternalColumns[OrderDate]',
    r'Package\DimProduct\Source.ExternalColumns[UnitPrice]',
]

print("=== _clean_col tests ===")
for s in samples:
    col = clean_col(s)
    typ = infer_col_type(col)
    print(f"  {col!r:25} -> type={typ}")
