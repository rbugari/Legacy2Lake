# Legacy2Lake Installation Guide 🛠️

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
    - Ensure your `.env` includes the following mandatory keys:
        - **Supabase**: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
        - **Cloudflare R2**: `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`.
        - **AI**: Azure OpenAI credentials (`AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`).

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
4.  Navigate to **Configuración de Inteligencia** and try the **Validation Playground** to ensure AI connectivity.
