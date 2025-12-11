/**
 * WebSocket Response Interfaces
 *
 * This file contains all the response type interfaces
 * for different WebSocket message types.
 */

import {
  WSMessageType,
  HumanMessageData,
  AIMessageData,
  ToolMessageData,
  AssistantMetricsData,
} from "./ws-types";

// ============================================
// WebSocket Response Interfaces
// ============================================

export interface ConnectedResponse {
  type: WSMessageType.CONNECTED;
  status: string;
  ws_id: string;  // Server-generated WebSocket ID (used for session + conversation memory)
  timestamp: number;
}

export interface QueryReceivedResponse {
  type: WSMessageType.QUERY_RECEIVED;
  ws_id: string;
  timestamp: number;
}

export interface HumanMessageResponse {
  type: WSMessageType.MESSAGE;
  data: HumanMessageData;
  ws_id: string;
  timestamp: number;
}

export interface AIMessageResponse {
  type: WSMessageType.MESSAGE;
  data: AIMessageData;
  ws_id: string;
  timestamp: number;
}

export interface ToolMessageResponse {
  type: WSMessageType.MESSAGE;
  data: ToolMessageData;
  ws_id: string;
  timestamp: number;
}

export interface FinalMessageResponse {
  type: WSMessageType.FINAL;
  data: AIMessageData;
  ws_id: string;
  timestamp: number;
}

export interface MetricsResponse {
  type: WSMessageType.METRICS;
  data: AssistantMetricsData;
  ws_id: string;
  timestamp: number;
}

export interface CompleteResponse {
  type: WSMessageType.COMPLETE;
  ws_id: string;
  timestamp: number;
}

export interface PongResponse {
  type: WSMessageType.PONG;
  timestamp?: number;
}

export interface ErrorResponse {
  type: WSMessageType.ERROR;
  data?: {
    message?: string;
    code?: string;
  };
  ws_id?: string;
  timestamp?: number;
}

// ============================================
// Union Types
// ============================================

export type MessageResponse = HumanMessageResponse | AIMessageResponse | ToolMessageResponse;

export type WSResponse =
  | ConnectedResponse
  | QueryReceivedResponse
  | MessageResponse
  | FinalMessageResponse
  | MetricsResponse
  | CompleteResponse
  | PongResponse
  | ErrorResponse;
