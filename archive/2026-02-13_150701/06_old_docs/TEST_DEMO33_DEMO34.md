# 🧪 TEST USUARIOS CUSTOMER3 - DEMO33 y DEMO34

## ✅ USUARIOS CREADOS

### 👑 MANAGER - DEMO33
```
Username: DEMO33
Email: rfbugari@gmail.com
Password: demo123
Role: MANAGER
Tenant: CUSTOMER3 (Customer Organization 3)
Status: ✅ Activo
```

### 👨‍💻 COLLABORATOR - DEMO34
```
Username: DEMO34
Email: ramirofbugari@gmail.com
Password: demo123
Role: COLLABORATOR
Tenant: CUSTOMER3 (Customer Organization 3)
Status: ✅ Activo
```

---

## 📊 CONTEXTO DEL TENANT CUSTOMER3

**Tenant ID:** `daac0ee6-3b28-412d-8acd-43ec51149188`
**Client ID:** `CUSTOMER3`
**Organización:** Customer Organization 3
**Plan:** STANDARD

### 🔌 Proveedores LLM Configurados
- **Azure OpenAI**
  - Base URL: `https://gpt4-testing-soprasteriaspain.openai.azure.com/`
  - API Key: `58132a497d104bc...` (enmascarado)
  - Status: ✅ Activo

### 📦 Modelos Habilitados (3 modelos)
1. **azure-gpt-35-turbo** (Azure)
2. **azure-gpt-4o** (Azure)
3. **gpt-4.1** (Azure)

### 👥 Usuarios del Tenant (3 usuarios)
1. **demo3** (demo3@demo.local) - MANAGER (original)
2. **DEMO33** (rfbugari@gmail.com) - MANAGER (nuevo)
3. **DEMO34** (ramirofbugari@gmail.com) - COLLABORATOR (nuevo)

---

## 🧪 TESTS EJECUTADOS

### ✅ Tests de Base de Datos (Completados)
- [x] Creación de usuario MANAGER (DEMO33)
- [x] Creación de usuario COLLABORATOR (DEMO34)
- [x] Verificación de usuarios en el tenant
- [x] Listar proveedores LLM del tenant
- [x] Listar modelos habilitados del tenant
- [x] Cambio de password (test y reversión)
- [x] Activar/Desactivar usuario (test y reversión)

### ⏳ Tests de API (Pendientes - requiere servidor corriendo)
- [ ] POST /api/auth/login (DEMO33)
- [ ] POST /api/auth/login (DEMO34)
- [ ] GET /api/auth/me
- [ ] GET /api/providers
- [ ] GET /api/models
- [ ] GET /api/projects
- [ ] POST /api/auth/change-password

### ⏳ Tests de UI (Pendientes)
- [ ] Login en la interfaz web con DEMO33
- [ ] Login en la interfaz web con DEMO34
- [ ] Verificar permisos de MANAGER vs COLLABORATOR
- [ ] Crear un proyecto como MANAGER
- [ ] Invitar COLLABORATOR a un proyecto

---

## 🚀 CÓMO PROBAR

### 1. Levantar el servidor API
```bash
python run.py
```

El servidor debería estar en: `http://localhost:8000`

### 2. Probar endpoints con el script de test
```bash
python test_api_endpoints.py
```

Este script probará:
- Login con DEMO33 y DEMO34
- Obtener contexto de usuario
- Listar proveedores, modelos y proyectos
- Cambio de password
- Diferencias de permisos entre MANAGER y COLLABORATOR

### 3. Probar desde la interfaz web

**Opción A: Login como MANAGER (DEMO33)**
1. Ir a: `http://localhost:3000` (o la URL de tu frontend)
2. Login con:
   - Username: `DEMO33`
   - Password: `demo123`
3. Verificar que puedes:
   - Ver proveedores LLM
   - Ver modelos habilitados
   - Crear proyectos
   - Invitar usuarios
   - Cambiar configuración del tenant

**Opción B: Login como COLLABORATOR (DEMO34)**
1. Login con:
   - Username: `DEMO34`
   - Password: `demo123`
2. Verificar que:
   - NO puedes ver proveedores LLM
   - NO puedes configurar modelos
   - Puedes ver proyectos (solo los asignados)
   - NO puedes invitar usuarios

---

## 📋 PERMISOS Y CAPACIDADES

### 👑 MANAGER (DEMO33)
**✅ PUEDE hacer:**
- Configurar proveedores LLM (agregar API keys)
- Habilitar/deshabilitar modelos
- Crear proyectos de migración
- Invitar COLLABORATOR/VIEWER a proyectos
- Crear otros MANAGERS del mismo tenant
- Ver y gestionar usuarios del tenant
- Usar agentes del sistema (Agent S, A, B...)
- Usar cartuchos de tecnología (SQL Server, Snowflake...)
- Cambiar su propia password

**❌ NO PUEDE hacer:**
- Crear nuevos agentes del sistema (requiere ADMIN)
- Agregar nuevos cartuchos de tecnología (requiere ADMIN)
- Ver/modificar otros tenants (requiere ADMIN)
- Cambiar el plan del tenant (requiere ADMIN)
- Impersonar otros usuarios (requiere ADMIN)

### 👨‍💻 COLLABORATOR (DEMO34)
**✅ PUEDE hacer:**
- Ver proyectos asignados
- Editar proyectos asignados
- Generar código en proyectos asignados
- Usar agentes del sistema
- Cambiar su propia password

**❌ NO PUEDE hacer:**
- Ver proveedores LLM
- Configurar modelos
- Crear proyectos
- Invitar usuarios
- Ver proyectos no asignados
- Cambiar configuración del tenant

---

## 💰 RESPONSABILIDAD DE GASTO

**IMPORTANTE:** El tenant CUSTOMER3 **PAGA** por:
- Todos los tokens consumidos por los 3 modelos Azure
- Todas las API calls a Azure OpenAI
- Uso de todos los usuarios del tenant (DEMO33, DEMO34, demo3)

El MANAGER (DEMO33 o demo3) es responsable de:
- Controlar quién invita al tenant
- Monitorear el consumo de tokens/API calls
- Gestionar el presupuesto del tenant

---

## 🔐 SEGURIDAD

### Passwords
- **Password actual:** `demo123` (temporal)
- **Recomendación:** Cambiar a password autogenerada en producción
- **Cambio de password:** Disponible vía API y UI

### Tokens de autenticación
- Los tokens JWT tienen expiración
- Se generan al hacer login exitoso
- Se invalidan al hacer logout

### Aislamiento de tenants
- DEMO33 y DEMO34 solo pueden ver datos de CUSTOMER3
- No pueden acceder a DEMO1, DEMO2 u otros tenants
- Los proveedores LLM son exclusivos del tenant

---

## 📝 PRÓXIMOS PASOS

1. **Ejecutar migración 022** (si no se ejecutó aún):
   ```sql
   -- En Supabase SQL Editor
   -- Ejecutar: supabase_migrations/022_v3.9_global_system_catalog.sql
   ```

2. **Levantar servidor API:**
   ```bash
   python run.py
   ```

3. **Probar endpoints:**
   ```bash
   python test_api_endpoints.py
   ```

4. **Probar UI:**
   - Login con DEMO33 (MANAGER)
   - Login con DEMO34 (COLLABORATOR)
   - Verificar permisos y capacidades

5. **Crear proyecto de prueba:**
   - Como DEMO33, crear proyecto: "Test Migration"
   - Source: SQL Server
   - Target: Snowflake
   - Invitar DEMO34 como COLLABORATOR

6. **Generar código:**
   - Como DEMO34, generar código en el proyecto
   - Verificar que funciona con modelos Azure

---

## 🐛 TROUBLESHOOTING

### El login falla
- Verificar que el servidor API está corriendo
- Verificar las credenciales (username/password)
- Verificar que el usuario está activo en la DB

### No se ven proveedores/modelos
- Verificar el role del usuario (COLLABORATOR no puede ver)
- Verificar que el tenant tiene proveedores configurados
- Verificar token de autenticación válido

### Error de permisos
- Verificar el role del usuario en la DB
- Verificar que el tenant_id es correcto
- Verificar que el usuario está asociado al tenant correcto

---

## 📞 CONTACTO

**Usuarios de prueba creados por:** Script `test_manager_operations.py`
**Fecha de creación:** 2026-02-09
**Tenant:** CUSTOMER3 (daac0ee6-3b28-412d-8acd-43ec51149188)

---

## ✅ CHECKLIST DE VERIFICACIÓN

- [x] Usuarios creados en base de datos
- [x] Passwords hasheadas con bcrypt
- [x] Usuarios asociados al tenant CUSTOMER3
- [x] Roles asignados correctamente (MANAGER y COLLABORATOR)
- [x] Usuarios activados (is_active = true)
- [x] Proveedores LLM verificados
- [x] Modelos habilitados verificados
- [ ] Login API probado
- [ ] Login UI probado
- [ ] Permisos verificados
- [ ] Proyecto de prueba creado
- [ ] Generación de código probada

---

**Estado:** ✅ USUARIOS CREADOS - LISTOS PARA PROBAR EN UI
