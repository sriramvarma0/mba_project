import { createContext, useContext, useEffect, useMemo, useState } from "react";

import api, { AUTH_EXPIRED_EVENT } from "../api/axios";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem("mba_token"));
  const [authReady, setAuthReady] = useState(false);
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("mba_user");
    return raw ? JSON.parse(raw) : null;
  });

  const clearAuth = () => {
    setToken(null);
    setUser(null);
  };

  useEffect(() => {
    if (token) {
      localStorage.setItem("mba_token", token);
    } else {
      localStorage.removeItem("mba_token");
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      localStorage.setItem("mba_user", JSON.stringify(user));
    } else {
      localStorage.removeItem("mba_user");
    }
  }, [user]);

  useEffect(() => {
    let isMounted = true;

    const hydrateSession = async () => {
      if (!token) {
        if (isMounted) {
          setAuthReady(true);
        }
        return;
      }

      try {
        const { data } = await api.get("/api/auth/me");
        if (isMounted) {
          setUser(data);
        }
      } catch (error) {
        if (isMounted) {
          clearAuth();
        }
      } finally {
        if (isMounted) {
          setAuthReady(true);
        }
      }
    };

    hydrateSession();

    return () => {
      isMounted = false;
    };
  }, [token]);

  useEffect(() => {
    const handleAuthExpired = () => {
      clearAuth();
    };

    window.addEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    return () => {
      window.removeEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    };
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post("/api/auth/login", { email, password });
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  };

  const register = async (payload) => {
    await api.post("/api/auth/register", payload);
  };

  const logout = () => {
    clearAuth();
  };

  const value = useMemo(
    () => ({
      token,
      user,
      authReady,
      isAdmin: user?.role === "admin",
      login,
      register,
      logout,
    }),
    [token, user, authReady]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
