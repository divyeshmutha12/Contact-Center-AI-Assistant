/**
 * Filtered Message Types and Storage
 *
 * This file contains interfaces for filtered/processed messages
 * and message storage structures.
 */

import { WSMessageType, MessageRole, MessageMetrics, FunctionCallContent } from "./ws-types";
import {
  WSResponse,
  ConnectedResponse,
  QueryReceivedResponse,
  CompleteResponse,
  HumanMessageResponse,
  AIMessageResponse,
  ToolMessageResponse,
  FinalMessageResponse,
  MetricsResponse,
  PongResponse,
  ErrorResponse,
} from "./ws-responses";
import { ChartConfig } from "./chart-types";

// ============================================
// Filtered Message Result
// ============================================

export interface FilteredMessage {
  type: WSMessageType;
  role?: MessageRole;
  wsId: string;  // Server-generated WebSocket ID (session + conversation memory)
  timestamp: number;
  // Extracted content based on message type
  content?: string;
  reasoning?: string[];
  functionCalls?: FunctionCallContent[];
  metrics?: MessageMetrics;
  agentName?: string;
  toolName?: string;
  errorCode?: string;
  // Chart data from final response
  chartData?: ChartConfig;
  // Original raw message for advanced use cases
  raw: WSResponse;
}

// ============================================
// Stored Messages by Type
// ============================================

export interface StoredMessages {
  connected: ConnectedResponse | null;
  queryReceived: QueryReceivedResponse[];
  humanMessages: FilteredMessage[];
  aiMessages: FilteredMessage[];
  toolMessages: FilteredMessage[];
  finalMessage: FilteredMessage | null;
  metricsMessage: FilteredMessage | null;
  complete: CompleteResponse | null;
  errors: FilteredMessage[];
  // All messages in order
  allMessages: FilteredMessage[];
}

// ============================================
// Callback Types
// ============================================

export type MessageCallback<T extends WSResponse = WSResponse> = (
  message: FilteredMessage,
  raw: T
) => void;

export interface MessageHandlerCallbacks {
  onConnected?: MessageCallback<ConnectedResponse>;
  onQueryReceived?: MessageCallback<QueryReceivedResponse>;
  onHumanMessage?: MessageCallback<HumanMessageResponse>;
  onAIMessage?: MessageCallback<AIMessageResponse>;
  onToolMessage?: MessageCallback<ToolMessageResponse>;
  onFinalMessage?: MessageCallback<FinalMessageResponse>;
  onMetrics?: MessageCallback<MetricsResponse>;
  onComplete?: MessageCallback<CompleteResponse>;
  onPong?: MessageCallback<PongResponse>;
  onError?: MessageCallback<ErrorResponse>;
  onAnyMessage?: MessageCallback<WSResponse>;
}
