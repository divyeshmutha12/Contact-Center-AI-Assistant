/**
 * WebSocket Message Handler - Barrel Export
 *
 * This file re-exports all WebSocket-related modules for convenient importing.
 * The handler has been split into separate files for better maintainability:
 *
 * - ws-types.ts: Enums and message data interfaces (WSMessageType, MessageRole, etc.)
 * - ws-responses.ts: WebSocket response interfaces (ConnectedResponse, etc.)
 * - chart-types.ts: Chart.js related interfaces (ChartConfig, ChartData, etc.)
 * - ws-filtered-types.ts: Filtered message and storage types
 * - ws-message-handler.ts: The WebSocketMessageHandler class
 */

// ============================================
// Re-export Enums and Message Types
// ============================================

export {
  WSMessageType,
  MessageRole,
} from "./ws-types";

export type {
  MessageMetrics,
  SummaryText,
  ReasoningContent,
  FunctionCallContent,
  TextContent,
  AIContentItem,
  HumanMessageData,
  AIMessageData,
  ToolMessageData,
  AssistantMetricsData,
} from "./ws-types";

// ============================================
// Re-export Response Types
// ============================================

export type {
  ConnectedResponse,
  QueryReceivedResponse,
  HumanMessageResponse,
  AIMessageResponse,
  ToolMessageResponse,
  FinalMessageResponse,
  MetricsResponse,
  CompleteResponse,
  PongResponse,
  ErrorResponse,
  MessageResponse,
  WSResponse,
} from "./ws-responses";

// ============================================
// Re-export Chart Types
// ============================================

export type {
  ChartDataset,
  ChartData,
  ChartOptions,
  ChartConfig,
} from "./chart-types";

// ============================================
// Re-export Filtered Types
// ============================================

export type {
  FilteredMessage,
  StoredMessages,
  MessageCallback,
  MessageHandlerCallbacks,
} from "./ws-filtered-types";

// ============================================
// Re-export Handler Class and Factory
// ============================================

export { WebSocketMessageHandler, createMessageHandler } from "./ws-message-handler";
