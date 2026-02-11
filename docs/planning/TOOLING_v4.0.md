# Legacy2Lake v4.0 - Tooling Strategy
## VSCode Native vs MCP Servers

**Fecha:** 2026-02-10  
**Autor:** Development Team  
**Status:** DECISIÓN FINAL  
**Contexto:** Definir herramientas necesarias para v4.0

---

## 🎯 DECISIÓN: NO NECESITAMOS MCP SERVERS

Después de analizar el entorno actual, **NO vamos a usar MCP servers** para v4.0.

### Razón Simple:
> **Todo lo que necesitamos ya está disponible en VSCode + Python nativo**

---

## ✅ INVENTARIO: LO QUE YA TENEMOS

### 1. **Database Access** ✅ RESUELTO
**Herramienta:** `connect_supabase_dev.py`

```python
# Ya tenemos acceso a Supabase
from connect_supabase_dev import get_supabase_client, get_postgres_connection

# Cliente Supabase (API)
supabase = get_supabase_client()
response = supabase.table('utm_tenants').select('*').execute()

# PostgreSQL directo (queries complejas)
conn = get_postgres_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM utm_system_prompts")
```

**Uso en v4.0:**
- ✅ Leer/escribir prompts en `utm_system_prompts`
- ✅ Ejecutar migrations
- ✅ Sync prompts (DB ↔ .md)
- ✅ Auditar cambios

**¿Necesitamos MCP?** ❌ NO - Ya funciona perfecto

---

### 2. **Filesystem Access** ✅ NATIVO

**Herramienta:** Python built-in + VSCode

```python
from pathlib import Path

# Leer/escribir prompts en markdown
prompt_file = Path("prompt_lab/cartridges/pyspark/bronze_layer.md")
content = prompt_file.read_text()

# Crear estructura de directorios
Path("prompt_lab/agents").mkdir(parents=True, exist_ok=True)
```

**Uso en v4.0:**
- ✅ Gestionar archivos `.md` en `prompt_lab/`
- ✅ Sync automático DB ↔ filesystem
- ✅ Version control de prompts

**¿Necesitamos MCP?** ❌ NO - Python nativo es suficiente

---

### 3. **Git Operations** ✅ INTEGRADO

**Herramienta:** VSCode Git + Python subprocess

```python
import subprocess

# Commit automático de prompts
def auto_commit_prompt(prompt_file: str):
    subprocess.run(["git", "add", prompt_file])
    subprocess.run(["git", "commit", "-m", f"Update prompt: {prompt_file}"])
    
# Ver historial
subprocess.run(["git", "log", "--oneline", prompt_file])
```

**Uso en v4.0:**
- ✅ Version control de prompts
- ✅ Commit automático al editar
- ✅ Diff entre versiones

**¿Necesitamos MCP?** ❌ NO - VSCode Git UI + subprocess

---

### 4. **Python Code Analysis** ✅ AST NATIVO

**Herramienta:** Python `ast` module

```python
import ast

def validate_generated_code(code: str) -> bool:
    """Valida sintaxis de código Python generado"""
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        print(f"Error: {e}")
        return False

def extract_imports(code: str) -> list:
    """Extrae imports de código Python"""
    tree = ast.parse(code)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend([alias.name for alias in node.names])
        elif isinstance(node, ast.ImportFrom):
            imports.append(f"{node.module}")
    return imports
```

**Uso en v4.0:**
- ✅ Validar código PySpark generado
- ✅ Extraer metadata (imports, funciones)
- ✅ Tests de equivalencia v3.9 vs v4.0

**¿Necesitamos MCP?** ❌ NO - AST nativo es poderoso

---

### 5. **AI Assistant** ✅ GITHUB COPILOT

**Herramienta:** Ya estás usando Copilot (yo)

**Capacidades:**
- ✅ Leer archivos del workspace
- ✅ Buscar código (grep/semantic search)
- ✅ Ejecutar comandos en terminal
- ✅ Crear/editar archivos
- ✅ Acceso a DB (via Python scripts)
- ✅ Git operations

**Uso en v4.0:**
- ✅ Asistir en extracción de prompts
- ✅ Generar migrations SQL
- ✅ Refactorizar cartridges
- ✅ Crear tests de equivalencia

**¿Necesitamos MCP?** ❌ NO - Copilot ya tiene todo

---

### 6. **Testing** ✅ PYTEST + PYTHON

**Herramienta:** pytest (ya instalado)

```python
# tests/test_prompt_migration.py

import pytest
from apps.api.services.refinement.cartridges.pyspark_cartridge import PySparkCartridge

class TestPromptMigration:
    """Test equivalencia v3.9 (hardcode) vs v4.0 (prompts)"""
    
    async def test_pyspark_bronze_equivalence(self):
        # Código v3.9 (baseline)
        expected_code = load_v39_baseline("bronze_example.py")
        
        # Código v4.0 (prompt-driven)
        cartridge = PySparkCartridge(project_id, registry)
        generated_code = await cartridge.generate_bronze(metadata)
        
        # Validar equivalencia
        assert validate_python_syntax(expected_code)
        assert validate_python_syntax(generated_code)
        assert extract_imports(expected_code) == extract_imports(generated_code)
        assert extract_metadata_columns(generated_code) == [
            "_ingestion_timestamp",
            "_ingestion_date", 
            "_source_file",
            "_source_system"
        ]
```

**Uso en v4.0:**
- ✅ Tests de equivalencia
- ✅ Validation de código generado
- ✅ Performance benchmarks

**¿Necesitamos MCP?** ❌ NO - pytest es estándar

---

### 7. **Documentation** ✅ MARKDOWN + VSCODE

**Herramienta:** VSCode Markdown Preview + Python

```python
# Script para generar docs automáticamente
from pathlib import Path

def generate_prompt_docs():
    """Auto-genera documentación de prompts"""
    prompts_dir = Path("prompt_lab/cartridges")
    
    for tech_dir in prompts_dir.iterdir():
        if tech_dir.is_dir():
            readme = tech_dir / "README.md"
            # Generar índice de prompts
            prompts = list(tech_dir.glob("*.md"))
            markdown = f"# {tech_dir.name}\n\n"
            markdown += "## Available Prompts:\n"
            for prompt in prompts:
                markdown += f"- [{prompt.stem}]({prompt.name})\n"
            
            readme.write_text(markdown)
```

**Uso en v4.0:**
- ✅ Documentar prompts
- ✅ Auto-generar índices
- ✅ Sync docs con código

**¿Necesitamos MCP?** ❌ NO - Markdown estándar

---

## 📦 LO QUE NO NECESITAMOS (Del plan original)

### ❌ MCP Servers Innecesarios:

| MCP Server | Razón para NO usar |
|------------|-------------------|
| `@mcp/server-postgres` | Ya tenemos `connect_supabase_dev.py` |
| `@mcp/server-filesystem` | Python `pathlib` es suficiente |
| `@mcp/server-git` | VSCode Git + subprocess |
| `@mcp/server-markdown` | VSCode Markdown Preview |
| `@mcp/server-github` | VSCode GitHub extension |
| `@mcp/server-memory` | Supabase DB para persistencia |
| Custom AST Parser | Python `ast` nativo |
| Custom Pytest Runner | `pytest` CLI directamente |
| Multi-Model Router | Lo hacemos en Python si es necesario |

**Conclusión:** 0/10 MCP servers son necesarios 🎉

---

## 🛠️ STACK DEFINITIVO PARA v4.0

### Backend (Python):
```
Python 3.11+
├── FastAPI (API server)
├── supabase-py (DB client)
├── psycopg2 (PostgreSQL directo)
├── pathlib (filesystem)
├── ast (code analysis)
├── subprocess (git ops)
└── pytest (testing)
```

### Frontend (TypeScript):
```
Next.js 14
├── React 18
├── TailwindCSS
├── Supabase JS client
└── VSCode (editor)
```

### Database:
```
Supabase PostgreSQL
└── connect_supabase_dev.py (connection helper)
```

### Development Tools:
```
VSCode
├── GitHub Copilot (AI assistant)
├── Git integration (version control)
├── Markdown Preview (docs)
├── Python extension
└── PowerShell terminal
```

**Total Complexity:** 🟢 BAJO (todo estándar industry)

---

## 🚀 SCRIPTS DE UTILIDAD PARA v4.0

Vamos a crear scripts Python simples en vez de MCP servers:

### 1. `scripts/sync_prompts.py`
```python
"""
Sync prompts entre filesystem (.md) y base de datos
Reemplaza necesidad de MCP filesystem + postgres
"""

from pathlib import Path
from connect_supabase_dev import get_supabase_client
import json

def sync_prompts_to_db():
    """Lee prompts de prompt_lab/ y los sube a DB"""
    supabase = get_supabase_client()
    prompt_lab = Path("prompt_lab")
    
    for md_file in prompt_lab.rglob("*.md"):
        # Parsear metadata del markdown
        content = md_file.read_text()
        metadata = parse_frontmatter(content)
        
        # Upsert en DB
        supabase.table('utm_system_prompts').upsert({
            'tech_id': metadata['tech_id'],
            'layer': metadata['layer'],
            'prompt_content': content,
            'source_file': str(md_file),
            'version': metadata['version']
        }).execute()
    
    print("✅ Prompts synced to DB")

def sync_prompts_from_db():
    """Backup: descarga prompts de DB a filesystem"""
    supabase = get_supabase_client()
    
    prompts = supabase.table('utm_system_prompts') \
        .select('*') \
        .execute()
    
    for prompt in prompts.data:
        file_path = Path(prompt['source_file'])
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(prompt['prompt_content'])
    
    print("✅ Prompts synced from DB")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "from-db":
        sync_prompts_from_db()
    else:
        sync_prompts_to_db()
```

**Uso:**
```powershell
# Subir prompts a DB
python scripts/sync_prompts.py

# Bajar prompts de DB (backup)
python scripts/sync_prompts.py from-db
```

---

### 2. `scripts/extract_prompts_v39.py`
```python
"""
Extrae templates hardcodeados de v3.9 y los convierte a prompts .md
Reemplaza necesidad de MCP AST parser
"""

import ast
from pathlib import Path

def extract_cartridge_prompts(cartridge_file: Path):
    """Extrae templates de un cartridge v3.9"""
    code = cartridge_file.read_text()
    tree = ast.parse(code)
    
    prompts = {}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            layer = node.name.replace("generate_", "")
            
            if layer in ["bronze", "silver", "gold"]:
                # Extraer docstring
                docstring = ast.get_docstring(node) or ""
                
                # Extraer return statement (template)
                template = extract_template_from_function(node)
                
                # Convertir a formato markdown
                prompts[layer] = create_prompt_markdown(
                    layer=layer,
                    docstring=docstring,
                    template=template
                )
    
    return prompts

def extract_all_cartridges():
    """Procesa todos los cartridges actuales"""
    cartridges_dir = Path("apps/api/services/refinement/cartridges")
    output_dir = Path("prompt_lab/cartridges")
    
    for cartridge_file in cartridges_dir.glob("*_cartridge.py"):
        tech_name = cartridge_file.stem.replace("_cartridge", "")
        print(f"Extracting {tech_name}...")
        
        prompts = extract_cartridge_prompts(cartridge_file)
        
        # Guardar en prompt_lab/
        tech_dir = output_dir / tech_name
        tech_dir.mkdir(parents=True, exist_ok=True)
        
        for layer, prompt_md in prompts.items():
            (tech_dir / f"{layer}_layer.md").write_text(prompt_md)
    
    print("✅ Extraction complete!")

if __name__ == "__main__":
    extract_all_cartridges()
```

**Uso:**
```powershell
# Extraer todos los prompts de v3.9
python scripts/extract_prompts_v39.py
```

---

### 3. `scripts/validate_generated_code.py`
```python
"""
Valida código generado por cartridges
Reemplaza necesidad de MCP AST validator
"""

import ast
from pathlib import Path
from typing import List, Dict

def validate_python_syntax(code: str) -> bool:
    """Valida si Python es sintácticamente correcto"""
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        print(f"❌ Syntax Error: {e}")
        return False

def validate_pyspark_code(code: str) -> Dict[str, bool]:
    """Validaciones específicas para PySpark"""
    checks = {
        'syntax_valid': validate_python_syntax(code),
        'has_spark_session': 'SparkSession' in code,
        'has_delta_format': 'format("delta")' in code,
        'has_metadata_columns': all([
            '_ingestion_timestamp' in code,
            '_ingestion_date' in code,
            '_source_file' in code,
            '_source_system' in code
        ]),
        'has_error_handling': 'try:' in code and 'except' in code,
        'has_logging': 'logger' in code or 'logging' in code
    }
    
    return checks

def validate_generated_output(output_dir: Path):
    """Valida todos los archivos generados en un directorio"""
    results = []
    
    for py_file in output_dir.rglob("*.py"):
        code = py_file.read_text()
        checks = validate_pyspark_code(code)
        
        all_passed = all(checks.values())
        status = "✅" if all_passed else "❌"
        
        print(f"{status} {py_file.name}")
        for check_name, passed in checks.items():
            if not passed:
                print(f"  ⚠️ {check_name}: FAILED")
        
        results.append({
            'file': str(py_file),
            'checks': checks,
            'passed': all_passed
        })
    
    # Resumen
    total = len(results)
    passed = sum(1 for r in results if r['passed'])
    print(f"\n📊 Summary: {passed}/{total} files passed")
    
    return results

if __name__ == "__main__":
    import sys
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output")
    validate_generated_output(output_dir)
```

**Uso:**
```powershell
# Validar código generado
python scripts/validate_generated_code.py output/project_123
```

---

### 4. `scripts/git_helper.py`
```python
"""
Helper para operaciones Git comunes
Reemplaza necesidad de MCP git server
"""

import subprocess
from pathlib import Path

def git_commit_prompts(message: str = "Update prompts"):
    """Commit automático de cambios en prompt_lab/"""
    subprocess.run(["git", "add", "prompt_lab/"])
    subprocess.run(["git", "commit", "-m", message])
    print(f"✅ Committed: {message}")

def git_diff_prompt(prompt_file: str):
    """Ver cambios en un prompt específico"""
    result = subprocess.run(
        ["git", "diff", f"prompt_lab/{prompt_file}"],
        capture_output=True,
        text=True
    )
    print(result.stdout)

def git_history_prompt(prompt_file: str, limit: int = 10):
    """Ver historial de cambios de un prompt"""
    result = subprocess.run(
        ["git", "log", f"--oneline", f"-{limit}", f"prompt_lab/{prompt_file}"],
        capture_output=True,
        text=True
    )
    print(result.stdout)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python git_helper.py <command> [args]")
        print("Commands: commit, diff, history")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "commit":
        message = sys.argv[2] if len(sys.argv) > 2 else "Update prompts"
        git_commit_prompts(message)
    
    elif command == "diff":
        prompt_file = sys.argv[2]
        git_diff_prompt(prompt_file)
    
    elif command == "history":
        prompt_file = sys.argv[2]
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        git_history_prompt(prompt_file, limit)
```

**Uso:**
```powershell
# Commit prompts
python scripts/git_helper.py commit "Update PySpark bronze prompt"

# Ver diff
python scripts/git_helper.py diff cartridges/pyspark/bronze_layer.md

# Ver historial
python scripts/git_helper.py history cartridges/pyspark/bronze_layer.md
```

---

## ✅ RESUMEN: TOOLING STACK FINAL

```
┌─────────────────────────────────────────────────┐
│ DESARROLLO v4.0 (Sin MCP Servers)               │
├─────────────────────────────────────────────────┤
│                                                 │
│ VSCode + GitHub Copilot                         │
│ ├── Python scripts (sync, extract, validate)   │
│ ├── connect_supabase_dev.py (DB access)        │
│ ├── pytest (testing)                            │
│ ├── Git integration (version control)          │
│ └── PowerShell terminal                         │
│                                                 │
└─────────────────────────────────────────────────┘

✅ Simple
✅ Estándar
✅ No dependencies adicionales
✅ Funciona AHORA
```

---

## 🎬 ACCIÓN INMEDIATA

### Esta Semana (Sprint 0):

1. ✅ **Crear scripts/** directory
2. ✅ **Implementar** 4 scripts:
   - `sync_prompts.py`
   - `extract_prompts_v39.py`
   - `validate_generated_code.py`
   - `git_helper.py`

3. ✅ **Ejecutar** extracción inicial:
   ```powershell
   python scripts/extract_prompts_v39.py
   python scripts/sync_prompts.py
   ```

4. ✅ **Verificar** que funciona con DB actual

**Timeline:** 1-2 días máximo

---

**Documento Status:** FINAL - Decisión tomada  
**Próxima Acción:** Crear scripts/ y empezar extracción  
**Owner:** Development Team  

---

*"Use the simplest tool that works. Don't add complexity until you need it."*
