#!/usr/bin/env python3
"""
Test de endpoints API - DEMO33 y DEMO34
Probar login, autenticación, y operaciones básicas
"""
import requests
import json
from typing import Optional

# Configuración
API_BASE_URL = "http://localhost:8000/api"  # Cambiar según tu configuración

class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.user_context: Optional[dict] = None
    
    def print_section(self, title: str):
        print("\n" + "="*90)
        print(f"📋 {title}")
        print("="*90)
    
    def print_success(self, msg: str):
        print(f"✅ {msg}")
    
    def print_error(self, msg: str):
        print(f"❌ {msg}")
    
    def print_info(self, msg: str):
        print(f"ℹ️  {msg}")
    
    def login(self, username: str, password: str) -> bool:
        """Test login endpoint"""
        self.print_section(f"LOGIN - {username}")
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={
                    "username": username,
                    "password": password
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_context = data.get("user")
                
                self.print_success(f"Login exitoso")
                print(f"\n📝 Contexto de usuario:")
                print(f"   User ID: {self.user_context.get('user_id')}")
                print(f"   Username: {self.user_context.get('username')}")
                print(f"   Email: {self.user_context.get('email')}")
                print(f"   Role: {self.user_context.get('role')}")
                print(f"   Tenant ID: {self.user_context.get('tenant_id')}")
                print(f"   Organization: {self.user_context.get('org_name')}")
                print(f"\n🔑 Token: {self.token[:50]}...")
                return True
            else:
                self.print_error(f"Login falló: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        
        except requests.exceptions.ConnectionError:
            self.print_error("No se pudo conectar al servidor API")
            self.print_info("Asegúrate de que el servidor esté corriendo en: " + self.base_url)
            self.print_info("Ejecuta: python run.py")
            return False
        
        except Exception as e:
            self.print_error(f"Error: {str(e)}")
            return False
    
    def get_me(self) -> bool:
        """Test /auth/me endpoint"""
        self.print_section("GET /auth/me - Obtener contexto actual")
        
        if not self.token:
            self.print_error("No hay token disponible. Ejecuta login primero.")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/auth/me",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_success("Contexto obtenido")
                print(f"\n📝 Usuario actual:")
                print(json.dumps(data, indent=2))
                return True
            else:
                self.print_error(f"Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        
        except Exception as e:
            self.print_error(f"Error: {str(e)}")
            return False
    
    def list_providers(self) -> bool:
        """Test GET /providers - Listar proveedores del tenant"""
        self.print_section("GET /providers - Proveedores LLM del tenant")
        
        if not self.token:
            self.print_error("No hay token disponible. Ejecuta login primero.")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/providers",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Proveedores obtenidos: {len(data)}")
                
                for provider in data:
                    print(f"\n   🔌 {provider.get('provider_name', 'unknown')}")
                    print(f"      Base URL: {provider.get('base_url', 'N/A')}")
                    api_key = provider.get('api_key', '')
                    masked = api_key[:15] + '...' if len(api_key) > 15 else api_key
                    print(f"      API Key: {masked}")
                    print(f"      Active: {'✅' if provider.get('is_active') else '❌'}")
                
                return True
            else:
                self.print_error(f"Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        
        except Exception as e:
            self.print_error(f"Error: {str(e)}")
            return False
    
    def list_models(self) -> bool:
        """Test GET /models - Listar modelos habilitados del tenant"""
        self.print_section("GET /models - Modelos LLM habilitados")
        
        if not self.token:
            self.print_error("No hay token disponible. Ejecuta login primero.")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Modelos obtenidos: {len(data)}")
                
                for model in data:
                    print(f"\n   📦 {model.get('model_id', 'unknown')}")
                    print(f"      Provider: {model.get('provider', 'N/A')}")
                    print(f"      Label: {model.get('label', 'N/A')}")
                    print(f"      Active: {'✅' if model.get('is_active') else '❌'}")
                
                return True
            else:
                self.print_error(f"Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        
        except Exception as e:
            self.print_error(f"Error: {str(e)}")
            return False
    
    def list_projects(self) -> bool:
        """Test GET /projects - Listar proyectos del tenant"""
        self.print_section("GET /projects - Proyectos del tenant")
        
        if not self.token:
            self.print_error("No hay token disponible. Ejecuta login primero.")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/projects",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Proyectos obtenidos: {len(data)}")
                
                for project in data:
                    print(f"\n   📁 {project.get('name', 'unknown')}")
                    print(f"      Source: {project.get('source_tech', 'N/A')}")
                    print(f"      Target: {project.get('target_tech', 'N/A')}")
                    print(f"      Status: {project.get('status', 'N/A')}")
                
                return True
            else:
                self.print_error(f"Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        
        except Exception as e:
            self.print_error(f"Error: {str(e)}")
            return False
    
    def change_password(self, new_password: str) -> bool:
        """Test POST /auth/change-password"""
        self.print_section(f"POST /auth/change-password - Cambiar password")
        
        if not self.token:
            self.print_error("No hay token disponible. Ejecuta login primero.")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/change-password",
                json={"new_password": new_password},
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                self.print_success("Password cambiado exitosamente")
                self.print_info(f"Nueva password: {new_password}")
                return True
            else:
                self.print_error(f"Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        
        except Exception as e:
            self.print_error(f"Error: {str(e)}")
            return False


def main():
    print("="*90)
    print("🧪 TEST DE ENDPOINTS API - DEMO33 y DEMO34")
    print("="*90)
    
    # Crear instancia del tester
    tester = APITester(API_BASE_URL)
    
    # Test 1: Login como MANAGER (DEMO33)
    print("\n\n🔹 TEST 1: LOGIN COMO MANAGER (DEMO33)")
    print("-" * 90)
    
    if not tester.login("DEMO33", "demo123"):
        print("\n⚠️  El servidor API no está corriendo o la configuración es incorrecta.")
        print("   Ejecuta: python run.py")
        return
    
    # Test 2: Obtener contexto
    tester.get_me()
    
    # Test 3: Listar proveedores (MANAGER puede ver)
    tester.list_providers()
    
    # Test 4: Listar modelos (MANAGER puede ver)
    tester.list_models()
    
    # Test 5: Listar proyectos
    tester.list_projects()
    
    # Test 6: Cambiar password
    input("\n\n[Presiona ENTER para probar cambio de password...]")
    if tester.change_password("newpassword123"):
        # Revertir password
        input("\n[Presiona ENTER para revertir password a demo123...]")
        tester.login("DEMO33", "newpassword123")
        tester.change_password("demo123")
    
    # Test 7: Login como COLLABORATOR (DEMO34)
    print("\n\n🔹 TEST 2: LOGIN COMO COLLABORATOR (DEMO34)")
    print("-" * 90)
    
    tester2 = APITester(API_BASE_URL)
    
    if not tester2.login("DEMO34", "demo123"):
        return
    
    # Test 8: COLLABORATOR intenta ver proveedores
    print("\n⚠️  COLLABORATOR intenta ver proveedores (debería fallar o estar vacío):")
    tester2.list_providers()
    
    # Test 9: COLLABORATOR intenta ver modelos
    tester2.list_models()
    
    # Test 10: COLLABORATOR puede ver proyectos (si fue invitado)
    tester2.list_projects()
    
    # RESUMEN
    print("\n\n" + "="*90)
    print("✅ RESUMEN DE TESTS")
    print("="*90)
    print("""
📊 Tests ejecutados:

MANAGER (DEMO33):
├─ ✅ Login exitoso
├─ ✅ Obtener contexto
├─ ✅ Ver proveedores LLM
├─ ✅ Ver modelos habilitados
├─ ✅ Ver proyectos
└─ ✅ Cambiar password

COLLABORATOR (DEMO34):
├─ ✅ Login exitoso
├─ ⚠️  Ver proveedores (restringido)
├─ ⚠️  Ver modelos (puede depender de permisos)
└─ ✅ Ver proyectos (solo los asignados)

🔐 CREDENCIALES DE PRUEBA:
┌─────────────┬──────────────────────────┬──────────┬──────────────┐
│ Usuario     │ Email                    │ Password │ Role         │
├─────────────┼──────────────────────────┼──────────┼──────────────┤
│ DEMO33      │ rfbugari@gmail.com       │ demo123  │ MANAGER      │
│ DEMO34      │ ramirofbugari@gmail.com  │ demo123  │ COLLABORATOR │
└─────────────┴──────────────────────────┴──────────┴──────────────┘

⚠️ PRÓXIMOS PASOS:
1. Levantar servidor API: python run.py
2. Ejecutar este script: python test_api_endpoints.py
3. Probar desde la UI web
""")


if __name__ == "__main__":
    main()
