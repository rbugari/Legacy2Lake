# Legacy2Lake Governance Rules (v3.8)
## 📋 Sistema de Ownership y Permisos

> **CRITICAL**: Este documento define las reglas de oro del sistema sobre quién es dueño de qué y quién puede modificar qué. **Estas reglas NO son negociables** y deben respetarse en toda implementación.

---

## 🏛️ Principios Fundamentales

### 1️⃣ **Separación de Responsabilidades**
- **ADMINISTRADOR**: Define infraestructura, tecnologías, y prompts base
- **TENANT**: Define proveedores, modelos, y costos
- **USUARIO/SOLUCIÓN**: Define personalizaciones específicas

### 2️⃣ **Coherencia del Catálogo**
- Solo se pueden usar tecnologías (orígenes/destinos) **existentes en el catálogo del sistema**
- **NO** se pueden inventar tecnologías ad-hoc
- Cualquier nueva tecnología debe ser creada formalmente por el administrador

### 3️⃣ **Control de Costos**
- La asignación de modelos a agentes es **responsabilidad del tenant**
- Cada tenant asume el costo de los modelos que configure
- El sistema debe permitir optimización de costos mediante selección inteligente de modelos

---

## 🔐 Ownership Matrix

### **Prompts de Agentes** (`utm_prompts` + `utm_agent_catalog`)
```
┌─────────────────────┬──────────────┬────────────┬──────────┐
│ Componente          │ Dueño        │ Visibilidad│ Edición  │
├─────────────────────┼──────────────┼────────────┼──────────┤
│ Prompt Base Agente  │ ADMIN        │ Todos      │ ADMIN    │
│ Configuración Agent │ ADMIN        │ Todos      │ ADMIN    │
│ Parámetros Generales│ ADMIN        │ Todos      │ ADMIN    │
└─────────────────────┴──────────────┴────────────┴──────────┘
```

**Regla**: Los prompts de los agentes son parte de la **lógica del sistema**. Nadie excepto el administrador puede modificarlos.

---

### **Prompts de Cartuchos (Tecnologías)** (`utm_cartridge_prompts`)
```
┌─────────────────────┬──────────────┬────────────┬──────────┐
│ Componente          │ Dueño        │ Visibilidad│ Edición  │
├─────────────────────┼──────────────┼────────────┼──────────┤
│ Prompt Base Cartucho│ ADMIN        │ Todos      │ ADMIN    │
│ Reglas Tecnología   │ ADMIN        │ Todos      │ ADMIN    │
│ Templates Generación│ ADMIN        │ Todos      │ ADMIN    │
└─────────────────────┴──────────────┴────────────┴──────────┘
```

**Regla**: Los cartuchos definen cómo generar código para cada tecnología. Son parte del **conocimiento técnico del sistema**.

---

### **Orígenes y Destinos (Catálogo de Tecnologías)** (`utm_system_catalog`)
```
┌─────────────────────┬──────────────┬────────────┬──────────┐
│ Componente          │ Dueño        │ Visibilidad│ Edición  │
├─────────────────────┼──────────────┼────────────┼──────────┤
│ Tecnología Origen   │ ADMIN        │ Todos      │ ADMIN    │
│ Tecnología Destino  │ ADMIN        │ Todos      │ ADMIN    │
│ Cartridge Config    │ ADMIN        │ Todos      │ ADMIN    │
└─────────────────────┴──────────────┴────────────┴──────────┘
```

**Reglas**:
1. ✅ **Solo** se pueden seleccionar orígenes/destinos que **existan en el catálogo**
2. ❌ **NO** se pueden crear orígenes/destinos ad-hoc en proyectos
3. 🔧 Para agregar una nueva tecnología, el **ADMIN** debe:
   - Crear entrada en `utm_system_catalog`
   - Definir el cartridge correspondiente
   - Crear el prompt base de la tecnología
   - Configurar reglas de generación

**Validación Obligatoria**:
```sql
-- Al crear/editar un proyecto, validar que las tecnologías existan
SELECT source_tech, target_tech 
FROM utm_projects 
WHERE source_tech NOT IN (SELECT tech_id FROM utm_system_catalog WHERE tech_type = 'source')
   OR target_tech NOT IN (SELECT tech_id FROM utm_system_catalog WHERE tech_type = 'destination');
-- Esta query DEBE retornar 0 filas
```

---

### **Tenant Configuration** (`utm_tenants`)
```
┌─────────────────────┬──────────────┬────────────┬──────────┐
│ Componente          │ Dueño        │ Visibilidad│ Edición  │
├─────────────────────┼──────────────┼────────────┼──────────┤
│ Tenant Info         │ ADMIN        │ Tenant     │ ADMIN    │
│ Relación Usuario    │ ADMIN        │ Tenant     │ ADMIN    │
│ Límites Tier        │ ADMIN        │ Tenant     │ ADMIN    │
└─────────────────────┴──────────────┴────────────┴──────────┘
```

**Modelo Actual (v3.7)**:
- Tenant : Usuario : Cliente = **1:1:1** (Un usuario por tenant)

**Modelo Futuro (v4.0+)**:
- Tenant : Usuario = **1:N** (Múltiples usuarios por tenant)
- Tenant : Cliente = **1:1** (Un cliente por tenant)

---

### **Provider Vault & Model Assignment** (`utm_provider_vault` + `utm_agent_matrix`)
```
┌─────────────────────┬──────────────┬────────────┬──────────┐
│ Componente          │ Dueño        │ Visibilidad│ Edición  │
├─────────────────────┼──────────────┼────────────┼──────────┤
│ Proveedores IA      │ TENANT       │ Tenant     │ Tenant   │
│ API Keys            │ TENANT       │ Tenant     │ Tenant   │
│ Modelos Custom      │ TENANT       │ Tenant     │ Tenant   │
│ Agent Matrix        │ TENANT       │ Tenant     │ Tenant   │
└─────────────────────┴──────────────┴────────────┴──────────┘
```

**Reglas**:
1. ✅ Cada **tenant** configura sus propios proveedores (Azure, OpenAI, Anthropic, etc.)
2. ✅ Cada **tenant** configura qué modelo usa cada agente (`utm_agent_matrix`)
3. 💰 **COST OWNERSHIP**: El tenant asume el costo de los modelos seleccionados
4. 🎯 **OPTIMIZATION**: El sistema debe recomendar asignaciones cost-effective

**Ejemplo de Estrategia de Costos**:
```
Agente A (Discovery)       → GPT-4o-mini      (Bajo costo, alta frecuencia)
Agente B (Context)         → GPT-4o-mini      (Bajo costo, alta frecuencia)
Agente C (Generation)      → GPT-4o           (Alto costo, calidad crítica)
Agente F (Compliance)      → Claude Sonnet    (Medio costo, razonamiento)
Agente G (Documentation)   → Llama 70B        (Bajo costo, formato simple)
```

**IMPORTANTE**: La configuración de modelos es **estratégica** porque impacta directamente en:
- 💵 Costos operacionales del tenant
- ⚡ Performance del sistema
- 🎯 Calidad de los outputs

---

### **Custom Prompts (3-Layer System)** (`utm_solution_prompts`)

El sistema de prompts funciona en **3 capas jerárquicas**:

```
┌─────────────────────────────────────────────────────────────┐
│ CAPA 1: AGENTE (Sistema)                                    │
│ Dueño: ADMIN                                                │
│ Ejemplo: "Eres Agent C, un generador de código PySpark..." │
└─────────────────────────────────────────────────────────────┘
                            ↓ (extends)
┌─────────────────────────────────────────────────────────────┐
│ CAPA 2: CARTUCHO (Tecnología)                               │
│ Dueño: ADMIN                                                │
│ Ejemplo: "Para Oracle → Spark, usa estos patterns..."      │
└─────────────────────────────────────────────────────────────┘
                            ↓ (extends)
┌─────────────────────────────────────────────────────────────┐
│ CAPA 3: CUSTOM (Solución)                                   │
│ Dueño: USUARIO/SOLUCIÓN                                     │
│ Ejemplo: "En esta empresa, usa prefijo 'stg_' para staging"│
└─────────────────────────────────────────────────────────────┘
```

**Composición Final**:
```python
final_prompt = (
    base_agent_prompt +        # Capa 1: ADMIN
    cartridge_prompt +         # Capa 2: ADMIN
    solution_custom_modifiers  # Capa 3: USUARIO
)
```

**Reglas**:
1. ✅ Las capas 1 y 2 son **inmutables** para el usuario
2. ✅ La capa 3 permite **modificadores** sin romper la lógica base
3. ✅ Los modificadores customizados deben ser **aditivos**, no reemplazar la lógica core

**Ejemplos de Modificadores Válidos (Capa 3)**:
```yaml
# Solution-Specific Modifiers
naming_conventions:
  - "Use prefix 'crm_' for all CRM-related tables"
  - "Suffix views with '_vw'"
  
business_rules:
  - "Apply currency conversion rate of 1.2 for USD→EUR"
  - "Mask SSN fields using SHA-256"
  
architectural_preferences:
  - "Prefer delta tables over parquet"
  - "Use checkpoint every 1000 records"
```

---

## 🚨 Validation Rules (Enforcement)

### **Rule 1: Technology Consistency Check**
```sql
-- Ejecutar en cada deploy/migration
SELECT 
    p.project_id,
    p.project_name,
    p.source_tech,
    p.target_tech
FROM utm_projects p
WHERE 
    p.source_tech NOT IN (
        SELECT tech_id FROM utm_system_catalog 
        WHERE tech_type = 'source' AND is_active = true
    )
    OR p.target_tech NOT IN (
        SELECT tech_id FROM utm_system_catalog 
        WHERE tech_type = 'destination' AND is_active = true
    );

-- Si retorna filas → DATA INCONSISTENCY DETECTED
```

### **Rule 2: Prompt Ownership Validation**
```sql
-- Prompts de agentes deben tener tenant_id = NULL (son globales)
SELECT * FROM utm_prompts 
WHERE prompt_type = 'agent' AND tenant_id IS NOT NULL;

-- Prompts custom deben tener tenant_id (son específicos)
SELECT * FROM utm_solution_prompts 
WHERE tenant_id IS NULL;
```

### **Rule 3: Provider Matrix Isolation**
```sql
-- Cada tenant solo puede ver sus propios proveedores
SELECT * FROM utm_provider_vault 
WHERE tenant_id = 'current_tenant_id';

-- Matrix debe referenciar proveedores válidos del tenant
SELECT am.*
FROM utm_agent_matrix am
LEFT JOIN utm_provider_vault pv 
    ON am.provider_id = pv.provider_id 
    AND am.tenant_id = pv.tenant_id
WHERE pv.provider_id IS NULL;
-- Si retorna filas → ORPHANED MATRIX ENTRIES
```

---

## 📊 Impact Analysis

### **Quién afecta a quién**:
```
ADMIN modifica Agente → Afecta a TODOS los tenants
ADMIN modifica Cartucho → Afecta a TODOS los proyectos de esa tecnología
TENANT modifica Provider → Afecta solo a sus proyectos
USUARIO modifica Custom Prompt → Afecta solo a esa solución
```

### **Blast Radius**:
```
┌──────────────────┬────────────────┬──────────────────────┐
│ Cambio           │ Scope          │ Requiere Aprobación  │
├──────────────────┼────────────────┼──────────────────────┤
│ Agent Prompt     │ GLOBAL         │ Change Control Board │
│ Cartridge Prompt │ PER-TECH       │ Tech Lead            │
│ Provider Config  │ PER-TENANT     │ Tenant Admin         │
│ Custom Modifier  │ PER-SOLUTION   │ Solution Owner       │
└──────────────────┴────────────────┴──────────────────────┘
```

---

## 🛠️ Implementation Checklist (v3.8)

- [ ] **Backend Validation Layer**:
  - [ ] Endpoint middleware para validar orígenes/destinos contra catálogo
  - [ ] API blocker si tecnología no existe en `utm_system_catalog`
  
- [ ] **UI Restrictions**:
  - [ ] Dropdowns de orígenes/destinos limitados a catálogo activo
  - [ ] Deshabilitar edición de prompts base para no-admins
  - [ ] Mostrar badge "ADMIN ONLY" en secciones restringidas

- [ ] **Database Constraints**:
  - [ ] Foreign keys entre `utm_projects.source_tech` → `utm_system_catalog.tech_id`
  - [ ] RLS policies para separar prompts globales vs tenant-specific

- [ ] **Diagnostic Tools**:
  - [ ] Script `check_governance_integrity.py` para auditar inconsistencias
  - [ ] Dashboard en Admin UI con alertas de incoherencias

- [ ] **Documentation**:
  - [x] Este documento (GOVERNANCE_RULES.md)
  - [ ] Actualizar INSTALL.md con sección de governance
  - [ ] Agregar diagrams a `docs/technical/`

---

## 🚀 Future Enhancements (v4.0)

- **Multi-User Tenants**: Soporte para N usuarios por tenant con roles diferenciados
- **Cost Analytics Dashboard**: Tracking de costos por tenant/modelo/agente en tiempo real
- **Template Marketplace**: Tenants pueden compartir custom modifiers (opt-in)
- **Prompt Versioning**: Control de versiones de prompts con rollback capability
- **A/B Testing**: Comparar outputs de diferentes asignaciones de modelos

---

> **⚠️ CRITICAL REMINDER**: Este sistema maneja **coherencia arquitectónica** y **control de costos**. Las reglas de governance NO son sugerencias, son **requisitos obligatorios** del sistema.

*Última actualización: 2026-02-06 (v3.8)*
