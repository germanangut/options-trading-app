import type { PropsWithChildren } from "react";
import { createContext, useContext, useEffect, useState } from "react";

import { ApiError } from "../../lib/apiClient";
import { getCurrentUser, login, logout, register } from "./api/authApi";
import { clearAuthToken, getAuthToken, setAuthToken } from "./authStorage";
import type { CredentialsPayload, CurrentUser } from "../../types/api";


type AuthStatus = "loading" | "authenticated" | "unauthenticated";

type AuthContextValue = {
  status: AuthStatus;
  currentUser: CurrentUser | null;
  login: (payload: CredentialsPayload) => Promise<void>;
  register: (payload: CredentialsPayload) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
};


const AuthContext = createContext<AuthContextValue | null>(null);


function isUnauthorizedError(error: unknown) {
  return error instanceof ApiError && error.status === 401;
}


export function AuthProvider({ children }: PropsWithChildren) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    const token = getAuthToken();

    if (!token) {
      setStatus("unauthenticated");
      return;
    }

    let cancelled = false;

    void getCurrentUser()
      .then((user) => {
        if (cancelled) {
          return;
        }

        setCurrentUser(user);
        setStatus("authenticated");
      })
      .catch((error) => {
        if (cancelled) {
          return;
        }

        if (isUnauthorizedError(error)) {
          clearAuthToken();
          setCurrentUser(null);
          setStatus("unauthenticated");
          return;
        }

        setCurrentUser(null);
        setStatus("unauthenticated");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function completeAuth(
    action: (payload: CredentialsPayload) => Promise<{
      access_token: string;
      user: CurrentUser;
    }>,
    payload: CredentialsPayload,
  ) {
    const session = await action(payload);
    setAuthToken(session.access_token);
    setCurrentUser(session.user);
    setStatus("authenticated");
  }

  async function handleLogout() {
    try {
      await logout();
    } finally {
      clearAuthToken();
      setCurrentUser(null);
      setStatus("unauthenticated");
    }
  }

  return (
    <AuthContext.Provider
      value={{
        status,
        currentUser,
        login: (payload) => completeAuth(login, payload),
        register: (payload) => completeAuth(register, payload),
        logout: handleLogout,
        isAuthenticated: status === "authenticated" && currentUser !== null,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}


export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider.");
  }

  return context;
}