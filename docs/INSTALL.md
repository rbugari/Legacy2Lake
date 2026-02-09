# Legacy2Lake Installation Guide 🛠️ (v3.7)

This guide covers the setup process for the Legacy2Lake platform (Backend API + Frontend Console).

## Prerequisites

- **Python**: 3.10 or higher.
- **Node.js**: 18.0 or higher.
- **Database**: Supabase PostgreSQL instance (Service Role Key required for maintenance tasks).
- **Storage**: Cloudflare R2 Bucket (S3-compatible API).
- **Environment**: Windows, Linux, or macOS.

---

## 1. Backend Setup (API)

The backend handles logic, AI orchestration, and cloud-native storage operations.

1.  **Navigate to the project root**:
    ```bash
    cd [project-dir]
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Configuration**:
    Create a `.env` file in the project root with the following mandatory keys:
    
    **Supabase (Metadata Store)**:
    ```env
    SUPABASE_URL=https://your-project.supabase.co
    SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
    ```
    
    **Cloudflare R2 (Object Storage)** - v3.5 Cloud-Native:
    ```env
    R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
    R2_ACCESS_KEY_ID=your-r2-access-key
    R2_SECRET_ACCESS_KEY=your-r2-secret-key
    R2_BUCKET_NAME=legacy2lake-artifacts
    ```
    > The R2 bucket stores all source artifacts, generated code, and certified output packages. Ensure it's created before starting.
    
    **AI Provider (Azure OpenAI or others)**:
    ```env
    AZURE_OPENAI_API_KEY=your-azure-key
    AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
    AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o  # or your deployment
    AZURE_OPENAI_API_VERSION=2024-05-01-preview
    ```
    
    **Optional Providers** (can be configured in Admin UI):
    ```env
    OPENAI_API_KEY=sk-...          # Direct OpenAI
    ANTHROPIC_API_KEY=sk-ant-...   # Claude
    GROQ_API_KEY=gsk_...            # Groq (Llama)
    ```

4.  **Start the Server**:
    ```bash
    python main.py
    ```
    - The API will start on `http://localhost:8085`.
    - Health Check: `http://localhost:8085/ping-antigravity`

---

## 2. Frontend Setup (Web Console)

The frontend provides the main dashboard, system administration, and artifact explorer.

1.  **Navigate to the Web directory**:
    ```bash
    cd apps/web
    ```

2.  **Install Dependencies**:
    ```bash
    npm install
    ```
    *(Note: If you encounter legacy peer dependency issues, use `npm install --legacy-peer-deps`)*

3.  **Start the Production Server**:
    We recommend using the custom Node.js server for stability.
    ```bash
    node server.js
    ```
    - The Dashboard will start on `http://localhost:3005`.

    *Alternatively, for development:*
    ```bash
    npm run dev
    ```

---

## 3. Verify Installation

1.  Open your browser to `http://localhost:3005`.
2.  Login with your configured credentials (or demo/demo if in dev mode).
3.  Navigate to **System Administration** and check that the **Origins** and **Destinations** lists are populated.
4.  Navigate to **Configuración de Inteligencia** and verify AI connectivity.

---

## 4. Post-Installation Configuration

### A. Provider Setup (Admin UI)

After installation, configure LLM providers in the Admin Panel (`/admin`):

1. **Add API Keys**: Navigate to **Provider Vault** and add keys for OpenAI, Groq, or other providers
2. **Create Models**: In **Model Catalog**, register available models (e.g., `gpt-4o`, `llama-3.1-70b`)
3. **Agent Assignments**: In **Agent Matrix**, assign specific models to each agent (Discovery, Context Builder, Code Generator, Compliance Auditor, Governance, Technology Scout)

### B. Technology Configuration

Configure supported source and destination technologies:

1. **Origins**: Ensure `utm_supported_techs` table has entries for your source systems (SQL Server, Oracle, SSIS, etc.)
2. **Destinations**: Verify target platforms are configured (Databricks, Snowflake, Fabric, etc.)
3. **Cartridges**: Check that cartridge files exist in `apps/utm/cartridges/` for your technologies

### C. R2 Bucket Structure

The system will automatically create the following structure in your R2 bucket:

```
<bucket-name>/
├── tenant-<uuid>/              # Per-tenant isolation
│   ├── projects/
│   │   ├── <project-id>/
│   │   │   ├── source/         # Uploaded artifacts
│   │   │   ├── generated/      # Output code
│   │   │   └── packages/       # COP bundles
```

---

> [!TIP]
> **Multi-Tenant Setup**: Each user gets isolated storage. The `tenant_id` from login determines the R2 prefix and RLS policies.
