import { create } from "zustand";
import { persist } from "zustand/middleware";
import { User, AuthTokens, LoginResponse } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

// Import chat store functions dynamically to avoid circular dependency
let resetChatStore: (() => void) | null = null;
let connectWebSocket: (() => void) | null = null;

export const setResetChatStore = (resetFn: () => void) => {
  resetChatStore = resetFn;
};

export const setConnectWebSocket = (connectFn: () => void) => {
  connectWebSocket = connectFn;
};

// ============================================
// Auth Store Interface
// ============================================

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoggingIn: boolean;
  loginError: string | null;

  login: (email: string, password: string, rememberMe?: boolean) => Promise<boolean>;
  logout: () => Promise<void>;
  clearError: () => void;
}

// ============================================
// Auth Store Implementation
// ============================================

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoggingIn: false,
      loginError: null,

      login: async (email: string, password: string, rememberMe = false) => {
        set({ isLoggingIn: true, loginError: null });

        try {
          const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              username: email,
              password,
            }),
          });

          if (!response.ok) {
            if (response.status === 401) {
              throw new Error("Invalid email or password");
            }
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || "Login failed");
          }

          const data: LoginResponse = await response.json();

          set({
            user: { name: data.username, email: email },
            tokens: {
              accessToken: data.token,
              refreshToken: null,
              tokenExpiry: null,
            },
            isAuthenticated: true,
            isLoggingIn: false,
            loginError: null,
          });

          // Auto-connect WebSocket after successful login
          if (connectWebSocket) {
            // Small delay to ensure state is updated
            setTimeout(() => {
              connectWebSocket!();
              console.log("[Auth] WebSocket auto-connected after login");
            }, 100);
          }

          return true;
        } catch (err) {
          const errorMsg = err instanceof Error ? err.message : "Login failed";
          set({ isLoggingIn: false, loginError: errorMsg });
          return false;
        }
      },

      logout: async () => {
        const { tokens } = get();

        try {
          if (tokens?.accessToken) {
            await fetch(`${API_BASE_URL}/api/auth/logout`, {
              method: "POST",
              headers: {
                // Authorization: `Bearer ${tokens.accessToken}`,
                "Content-Type": "application/json",
              },
              body: JSON.stringify({ token: tokens.accessToken }),
            });
          }
        } catch (err) {
          console.error("Logout error:", err);
        } finally {
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
            loginError: null,
          });
          // Reset chat store on logout
          if (resetChatStore) {
            resetChatStore();
          }
        }
      },

      clearError: () => set({ loginError: null }),
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({
        user: state.user,
        tokens: state.tokens,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
