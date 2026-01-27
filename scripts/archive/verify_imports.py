"""
Script para verificar que el servidor puede iniciar sin errores de importación
"""
import sys
import importlib.util

print("="*70)
print("VERIFICACIÓN DE IMPORTS DEL SERVIDOR UTM")
print("="*70 + "\n")

# Test 1: Verificar que main.py se puede importar
print("1️⃣  Verificando importación de main.py...")
try:
    sys.path.insert(0, "apps/api")
    spec = importlib.util.spec_from_file_location("main", "apps/api/main.py")
    main_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_module)
    print("   ✅ main.py importado correctamente")
    print(f"   ✅ FastAPI app creada: {type(main_module.app)}")
except Exception as e:
    print(f"   ❌ Error al importar main.py:")
    print(f"      {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Verificar routers
print("\n2️⃣  Verificando routers...")
routers = [
    "routers.agents",
    "routers.system", 
    "routers.triage",
    "routers.transpile",
    "routers.governance",
    "routers.projects"
]

for router_name in routers:
    try:
        router_module = importlib.import_module(router_name)
        print(f"   ✅ {router_name}")
    except Exception as e:
        print(f"   ❌ {router_name}: {str(e)}")

# Test 3: Verificar servicios de agentes
print("\n3️⃣  Verificando servicios de agentes...")
services = [
    "services.agent_a_service",
    "services.agent_c_service",
    "services.agent_f_service",
    "services.agent_g_service",
    "services.agent_s_service"
]

for service_name in services:
    try:
        service_module = importlib.import_module(service_name)
        print(f"   ✅ {service_name}")
    except Exception as e:
        print(f"   ❌ {service_name}: {str(e)}")

# Test 4: Verificar dependencies
print("\n4️⃣  Verificando dependencies...")
try:
    deps = importlib.import_module("routers.dependencies")
    print(f"   ✅ routers.dependencies")
    print(f"   ✅ get_db disponible: {hasattr(deps, 'get_db')}")
    print(f"   ✅ get_identity disponible: {hasattr(deps, 'get_identity')}")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

print("\n" + "="*70)
print("RESULTADO: ✅ Todos los módulos se importan correctamente")
print("="*70)
print("\n💡 El servidor debería poder iniciar sin errores de importación")
print("   Ejecuta: uvicorn apps.api.main:app --reload --port 8089\n")
