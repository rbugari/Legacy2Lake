#!/usr/bin/env python3
"""
Verificar que .env NO contenga credenciales LLM (deben estar en DB)
"""
import os
import re
from pathlib import Path


def check_env_file():
    """Verifica que .env no contenga credenciales LLM"""
    
    print("="*80)
    print("VERIFICACIÓN: Variables de entorno (.env)")
    print("="*80)
    
    env_file = Path(".env")
    
    if not env_file.exists():
        print("⚠️  Archivo .env no encontrado")
        return
    
    content = env_file.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    # Variables que NO deberían estar en .env (v3.9+)
    forbidden_vars = {
        'OPENAI_API_KEY': 'utm_provider_vault',
        'GROQ_API_KEY': 'utm_provider_vault',
        'AZURE_OPENAI_API_KEY': 'utm_provider_vault',
        'ANTHROPIC_API_KEY': 'utm_provider_vault',
        'GOOGLE_API_KEY': 'utm_provider_vault',
        'AZURE_OPENAI_ENDPOINT': 'utm_provider_vault',
        'AZURE_OPENAI_DEPLOYMENT_ID': 'utm_provider_vault',
        'AZURE_OPENAI_API_VERSION': 'utm_provider_vault',
        'DEFAULT_MODEL': 'utm_model_catalog',
        'MODEL_NAME': 'utm_model_catalog',
        'OPENAI_MODEL': 'utm_model_catalog',
    }
    
    # Variables que SÍ deben estar en .env
    required_vars = {
        'SUPABASE_URL': 'Infraestructura - Base de datos',
        'SUPABASE_SERVICE_ROLE_KEY': 'Infraestructura - Base de datos',
        'STORAGE_PROVIDER': 'Infraestructura - Almacenamiento',
    }
    
    print("\n✅ VARIABLES REQUERIDAS (Infraestructura)")
    print("-" * 80)
    
    for var, desc in required_vars.items():
        # Check if variable exists and is not commented
        pattern = rf'^{var}='
        found = False
        for line in lines:
            if re.match(pattern, line.strip()) and not line.strip().startswith('#'):
                found = True
                # Mask the value
                parts = line.split('=', 1)
                if len(parts) == 2:
                    value = parts[1].strip('"\'')
                    masked = value[:10] + '...' if len(value) > 10 else value
                    print(f"✅ {var} = {masked}")
                break
        
        if not found:
            print(f"⚠️  {var} NO encontrada")
    
    print("\n❌ VARIABLES PROHIBIDAS (Deben estar en DB)")
    print("-" * 80)
    
    found_forbidden = []
    for var, table in forbidden_vars.items():
        # Check if variable exists and is NOT commented
        pattern = rf'^{var}='
        for line in lines:
            if re.match(pattern, line.strip()) and not line.strip().startswith('#'):
                found_forbidden.append((var, table, line.strip()))
                break
    
    if found_forbidden:
        print("\n⚠️  ENCONTRADAS VARIABLES QUE DEBERÍAN ESTAR EN DB:\n")
        for var, table, line in found_forbidden:
            print(f"❌ {var}")
            print(f"   Línea: {line}")
            print(f"   Debe ir en: {table} (por tenant)")
            print()
        
        print(f"\n{'='*80}")
        print("🔧 ACCIÓN REQUERIDA")
        print('='*80)
        print("""
Las credenciales LLM deben estar en la BASE DE DATOS, no en .env.

Pasos para migrar:
1. Comentar/eliminar estas variables de .env
2. Cada tenant configura sus propias API keys vía:
   - UI: Settings → Provider Vault
   - SQL: INSERT INTO utm_provider_vault (...)

Razón:
- Cada tenant tiene sus propias API keys
- Cada tenant paga por su propio uso
- No hay credenciales compartidas
- Aislamiento completo entre clientes

Ver documentación: docs/ENV_VS_DATABASE.md
""")
    else:
        print("\n✅ PERFECTO: No hay credenciales LLM en .env")
        print("   Todas las API keys deben estar en utm_provider_vault (DB)")
    
    # Check for commented forbidden vars (migration in progress)
    print("\n💬 VARIABLES COMENTADAS (migración en progreso)")
    print("-" * 80)
    
    commented_forbidden = []
    for var in forbidden_vars.keys():
        pattern = rf'#\s*{var}='
        for line in lines:
            if re.match(pattern, line.strip()):
                commented_forbidden.append((var, line.strip()))
                break
    
    if commented_forbidden:
        print("\n✅ Variables comentadas correctamente (ya migradas a DB):\n")
        for var, line in commented_forbidden:
            print(f"   {var}")
    else:
        print("   (ninguna)")
    
    print("\n" + "="*80)
    print("RESUMEN")
    print("="*80)
    print(f"""
✅ Variables requeridas encontradas: {sum(1 for v in required_vars if any(re.match(rf'^{v}=', l.strip()) and not l.strip().startswith('#') for l in lines))} / {len(required_vars)}
❌ Variables prohibidas encontradas: {len(found_forbidden)}
💬 Variables comentadas (OK): {len(commented_forbidden)}

Archivo .env: {'✅ CORRECTO' if len(found_forbidden) == 0 else '⚠️ NECESITA LIMPIEZA'}
""")


if __name__ == "__main__":
    check_env_file()
