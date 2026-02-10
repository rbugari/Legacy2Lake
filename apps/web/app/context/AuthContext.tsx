"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

interface User {
  tenant_id: string;
  display_name: string;  // Organization display name
  role: string;
  username: string; // Added for display
}

interface AuthContextType {
  user: User | null;
  login: (tenant_id: string, display_name: string, role: string, username: string) => void;
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
    const displayName = localStorage.getItem("x_display_name");
    const role = localStorage.getItem("x_role") || "USER";
    const username = localStorage.getItem("x_username") || "User";

    if (tenant && displayName) {
      setUser({ tenant_id: tenant, display_name: displayName, role, username });
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (loading) return;

    // 2. Protect Routes
    const publicRoutes = ["/login", "/", "/help"];
    const isPublicPath = publicRoutes.includes(pathname) || pathname.startsWith("/help");
    const isAdminRoute = pathname.startsWith("/admin");

    if (!user && !isPublicPath) {
      router.push("/login");
    } else if (user && isAdminRoute && user.role !== "ADMIN") {
      router.push("/dashboard"); // Unauthorized: Back to safety
    }
  }, [user, loading, pathname, router]);

  const login = (tenant_id: string, display_name: string, role: string, username: string) => {
    localStorage.setItem("x_tenant_id", tenant_id);
    localStorage.setItem("x_display_name", display_name);
    localStorage.setItem("x_role", role);
    localStorage.setItem("x_username", username);

    setUser({ tenant_id, display_name, role, username });
    router.push("/dashboard"); // Default redirect
  };

  const logout = () => {
    localStorage.removeItem("x_tenant_id");
    localStorage.removeItem("x_display_name");
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
