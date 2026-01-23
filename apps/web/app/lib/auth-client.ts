
import { API_BASE_URL } from "./config";

export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
    // 1. Get Credentials from LocalStorage
    const tenant_id = localStorage.getItem("x_tenant_id");
    const client_id = localStorage.getItem("x_client_id");

    // 2. Prepare Headers
    const headers: HeadersInit = {
        ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...(options.headers || {}),
    };

    if (tenant_id && !(headers as any)["X-Tenant-ID"]) {
        (headers as any)["X-Tenant-ID"] = tenant_id;
    }
    if (client_id) {
        (headers as any)["X-Client-ID"] = client_id;
    }

    // 3. Construct URL
    // Ensure endpoint allows leading slash or not
    const path = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    const url = `${API_BASE_URL}${path}`;

    // 4. Exec
    const res = await fetch(url, {
        ...options,
        headers,
    });

    // 5. Global Error Handling (Optional: Redirect on 401/403)
    if (res.status === 401 || res.status === 403) {
        // Logic to force logout could go here, but context handles it mostly.
        // For now just return.
    }

    return res;
}
