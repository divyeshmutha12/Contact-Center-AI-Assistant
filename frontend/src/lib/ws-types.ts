/**
 * WebSocket Message Types and Enums
 *
 * This file contains all the core enums and message data interfaces
 * used for WebSocket communication.
 */

// ============================================
// Message Type Enums
// ============================================

export enum WSMessageType {
  CONNECTION = "connection",
  CONNECTED = "connected",
  QUERY_RECEIVED = "query_received",
  MESSAGE = "message",
  STREAM = "stream",
  TOOL_START = "tool_start",
  TOOL_END = "tool_end",
  FINAL = "final",
  COMPLETE = "complete",
  PONG = "pong",
  ERROR = "error",
  METRICS = "metrics",
}

export enum MessageRole {
  HUMAN = "human",
  AI = "ai",
  ASSISTANT = "assistant",
  TOOL = "tool",
}

// ============================================
// Metric Interfaces
// ============================================

export interface MessageMetrics {
  latency_seconds: number;
  latency_ms: number;
  tokens?: number;
  input_tokens: number;
  output_tokens: number;
  cost?: number;
  total_tokens?: number;
  total_cost?: number;
  message_count?: number;
  provider?: string;
}

// ============================================
// AI Content Types
// ============================================

export interface SummaryText {
  text: string;
  type: "summary_text";
}

export interface ReasoningContent {
  id: string;
  summary: SummaryText[];
  type: "reasoning";
}

export interface FunctionCallContent {
  arguments: string;
  call_id: string;
  name: string;
  type: "function_call";
  id: string;
  status: string;
}

export interface TextContent {
  type: "text";
  text: string;
  annotations?: unknown[];
  id?: string;
}

export type AIContentItem = ReasoningContent | FunctionCallContent | TextContent;

// ============================================
// Message Data Interfaces
// ============================================

export interface HumanMessageData {
  content: string;
  role: MessageRole.HUMAN;
  metrics: MessageMetrics;
}

export interface AIMessageData {
  content: string | AIContentItem[];
  role: MessageRole.AI;
  metrics: MessageMetrics;
  agent_name?: string;
}

export interface ToolMessageData {
  content: string;
  role: MessageRole.TOOL;
  metrics: MessageMetrics;
  tool_name: string;
}

export interface AssistantMetricsData {
  content: string;
  role: MessageRole.ASSISTANT;
  metrics: MessageMetrics;
}
