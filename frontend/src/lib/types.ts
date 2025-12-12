import { ChartConfig, ReportPath } from "./websocket-message-handler";

// ============================================
// User & Authentication Types
// ============================================

export interface User {
  id?: string;
  username?: string;
  email?: string;
  name?: string;
  full_name?: string | null;
  role?: string;
  is_active?: boolean;
  created_at?: string;
  last_login?: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken?: string | null;
  tokenExpiry?: number | null;
}

export interface LoginResponse {
  token: string;
  username: string;
  status: string;
}

// ============================================
// Chat & Message Types
// ============================================

// Thinking step for thought process display
export interface ThinkingStep {
  id: string;
  agentName: string;
  reasoning: string[];
  functionCalls: { name: string; arguments: string; status: string }[];
  timestamp: number;
}

// Response version for retry feature - stores multiple responses for same query
export interface ResponseVersion {
  id: string;
  content: string;
  timestamp: Date;
  chartData?: ChartConfig;
  reportPath?: ReportPath;
  thinkingSteps?: ThinkingStep[];
}

export interface Message {
  id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: Date;
  // For assistant messages: multiple response versions (retry feature)
  responseVersions?: ResponseVersion[];
  currentVersionIndex?: number;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  // Note: conversation memory is handled by ws_id on the backend
  // Each WebSocket connection = one conversation thread
}
