"use client";

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
} from "react";

// Types for messages
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  username: string | null;
}

interface FlaskChatContextType {
  // Auth state
  auth: AuthState;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;

  // Chat state
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;

  // Chat actions
  sendMessage: (message: string) => Promise<void>;
  clearMessages: () => void;
}

const FlaskChatContext = createContext<FlaskChatContextType | undefined>(
  undefined
);

// API Base URL - change this to match your Flask backend
const API_URL = process.env.NEXT_PUBLIC_FLASK_API_URL || "http://localhost:8000";

export function FlaskChatProvider({ children }: { children: ReactNode }) {
  // Auth state - always start as not authenticated
  // User must click "Sign In" to login, no auto-login from localStorage
  const [auth, setAuth] = useState<AuthState>({
    isAuthenticated: false,
    token: null,
    username: null,
  });

  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Login function
  const login = useCallback(
    async (username: string, password: string): Promise<boolean> => {
      try {
        setError(null);
        const res = await fetch(`${API_URL}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });

        const data = await res.json();

        if (res.ok && data.status === "success") {
          const newAuth = {
            isAuthenticated: true,
            token: data.token,
            username: data.username,
          };
          setAuth(newAuth);

          // Save to localStorage
          localStorage.setItem("flask_token", data.token);
          localStorage.setItem("flask_username", data.username);

          return true;
        } else {
          setError(data.error || "Login failed");
          return false;
        }
      } catch (err) {
        setError("Failed to connect to server");
        return false;
      }
    },
    []
  );

  // Logout function
  const logout = useCallback(async (): Promise<void> => {
    try {
      if (auth.token) {
        await fetch(`${API_URL}/auth/logout`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token: auth.token }),
        });
      }
    } catch (err) {
      console.error("Logout error:", err);
    } finally {
      // Clear state regardless of API response
      setAuth({
        isAuthenticated: false,
        token: null,
        username: null,
      });
      setMessages([]);
      setError(null);
      localStorage.removeItem("flask_token");
      localStorage.removeItem("flask_username");
    }
  }, [auth.token]);

  // Send message function
  const sendMessage = useCallback(
    async (message: string): Promise<void> => {
      if (!auth.token || !message.trim()) return;

      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: message.trim(),
        timestamp: new Date(),
      };

      // Add user message immediately
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        const res = await fetch(`${API_URL}/chat/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            token: auth.token,
            message: message.trim(),
          }),
        });

        const data = await res.json();

        if (res.ok && data.status === "success") {
          // Check if the reply contains error indicators and show generic message
          const replyContent = data.reply || "";
          const isErrorResponse =
            replyContent.toLowerCase().includes("an error occurred:") ||
            replyContent.toLowerCase().includes("connection string is not valid") ||
            replyContent.toLowerCase().includes("error:") ||
            replyContent.toLowerCase().includes("exception") ||
            replyContent.toLowerCase().includes("traceback");

          const assistantMessage: ChatMessage = {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            content: isErrorResponse ? "Some Error Occurred. Please try again later." : replyContent,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, assistantMessage]);
        } else {
          // Handle auth error
          if (res.status === 401) {
            setError("Session expired. Please login again.");
            await logout();
          } else {
            setError("Some Error Occurred");
          }
        }
      } catch (err) {
        setError("Failed to connect to server");
      } finally {
        setIsLoading(false);
      }
    },
    [auth.token, logout]
  );

  // Clear messages
  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  const value: FlaskChatContextType = {
    auth,
    login,
    logout,
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
  };

  return (
    <FlaskChatContext.Provider value={value}>
      {children}
    </FlaskChatContext.Provider>
  );
}

export function useFlaskChat(): FlaskChatContextType {
  const context = useContext(FlaskChatContext);
  if (context === undefined) {
    throw new Error("useFlaskChat must be used within a FlaskChatProvider");
  }
  return context;
}
