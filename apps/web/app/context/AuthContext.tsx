"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

interface User {
  tenant_id: string;
  client_id: string;
  role: string;
  username: string; // Added for display
}

interface AuthContextType {
  user: User | null;
  login: (tenant_id: string, client_id: string, role: string, username: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  login: () => { },
  logout: () => { },
  isAuthenticated: false,
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();
  const pathname = usePathname();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Check LocalStorage on init
    const tenant = localStorage.getItem("x_tenant_id");
    const client = localStorage.getItem("x_client_id");
    const role = localStorage.getItem("x_role") || "USER";
    const username = localStorage.getItem("x_username") || "User";

    if (tenant && client) {
      setUser({ tenant_id: tenant, client_id: client, role, username });
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (loading) return;

    // 2. Protect Routes
    const publicRoutes = ["/login"];
    const isAdminRoute = pathname.startsWith("/admin");

    if (!user && !publicRoutes.includes(pathname)) {
      router.push("/login");
    } else if (user && isAdminRoute && user.role !== "ADMIN") {
      router.push("/dashboard"); // Unauthorized: Back to safety
    }
  }, [user, loading, pathname, router]);

  const login = (tenant_id: string, client_id: string, role: string, username: string) => {
    localStorage.setItem("x_tenant_id", tenant_id);
    localStorage.setItem("x_client_id", client_id);
    localStorage.setItem("x_role", role);
    localStorage.setItem("x_username", username);

    setUser({ tenant_id, client_id, role, username });
    router.push("/dashboard"); // Default redirect
  };

  const logout = () => {
    localStorage.removeItem("x_tenant_id");
    localStorage.removeItem("x_client_id");
    localStorage.removeItem("x_role");
    localStorage.removeItem("x_username");
    setUser(null);
    router.push("/login"); // Fixed: Redirect to login on logout
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};
