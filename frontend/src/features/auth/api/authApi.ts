import { apiClient } from "../../../lib/apiClient";
import type { AuthSession, CredentialsPayload, CurrentUser } from "../../../types/api";


export function register(payload: CredentialsPayload): Promise<AuthSession> {
  return apiClient.post<AuthSession>("/auth/register", payload);
}


export function login(payload: CredentialsPayload): Promise<AuthSession> {
  return apiClient.post<AuthSession>("/auth/login", payload);
}


export function logout(): Promise<{ success: boolean }> {
  return apiClient.post<{ success: boolean }>("/auth/logout", {});
}


export function getCurrentUser(): Promise<CurrentUser> {
  return apiClient.get<CurrentUser>("/auth/me");
}