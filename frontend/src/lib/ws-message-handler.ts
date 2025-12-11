/**
 * WebSocket Message Handler Class
 *
 * This file contains the main WebSocketMessageHandler class
 * responsible for parsing, filtering, and storing WebSocket messages.
 */

import { WSMessageType, MessageRole, FunctionCallContent } from "./ws-types";
import {
  WSResponse,
  ConnectedResponse,
  QueryReceivedResponse,
  CompleteResponse,
  MessageResponse,
  HumanMessageResponse,
  AIMessageResponse,
  ToolMessageResponse,
  FinalMessageResponse,
  MetricsResponse,
  PongResponse,
  ErrorResponse,
} from "./ws-responses";
import { ChartConfig } from "./chart-types";
import { FilteredMessage, StoredMessages, MessageHandlerCallbacks } from "./ws-filtered-types";

// ============================================
// WebSocket Message Handler Class
// ============================================

export class WebSocketMessageHandler {
  private callbacks: MessageHandlerCallbacks = {};
  private storedMessages: StoredMessages;

  constructor(callbacks?: MessageHandlerCallbacks) {
    if (callbacks) {
      this.callbacks = callbacks;
    }
    this.storedMessages = this.createEmptyStorage();
  }

  private createEmptyStorage(): StoredMessages {
    return {
      connected: null,
      queryReceived: [],
      humanMessages: [],
      aiMessages: [],
      toolMessages: [],
      finalMessage: null,
      metricsMessage: null,
      complete: null,
      errors: [],
      allMessages: [],
    };
  }

  // Reset stored messages (call when starting a new query)
  resetMessages(): void {
    this.storedMessages = this.createEmptyStorage();
  }

  // Get all stored messages
  getStoredMessages(): StoredMessages {
    return this.storedMessages;
  }

  // Get the final response text (from type "final" with role "ai")
  getFinalResponseText(): string | null {
    if (!this.storedMessages.finalMessage) {
      return null;
    }
    return this.storedMessages.finalMessage.content || null;
  }

  // ============================================
  // Callback Registration Methods
  // ============================================

  onConnected(callback: (message: FilteredMessage, raw: ConnectedResponse) => void): this {
    this.callbacks.onConnected = callback;
    return this;
  }

  onQueryReceived(callback: (message: FilteredMessage, raw: QueryReceivedResponse) => void): this {
    this.callbacks.onQueryReceived = callback;
    return this;
  }

  onHumanMessage(callback: (message: FilteredMessage, raw: HumanMessageResponse) => void): this {
    this.callbacks.onHumanMessage = callback;
    return this;
  }

  onAIMessage(callback: (message: FilteredMessage, raw: AIMessageResponse) => void): this {
    this.callbacks.onAIMessage = callback;
    return this;
  }

  onToolMessage(callback: (message: FilteredMessage, raw: ToolMessageResponse) => void): this {
    this.callbacks.onToolMessage = callback;
    return this;
  }

  onFinalMessage(callback: (message: FilteredMessage, raw: FinalMessageResponse) => void): this {
    this.callbacks.onFinalMessage = callback;
    return this;
  }

  onMetrics(callback: (message: FilteredMessage, raw: MetricsResponse) => void): this {
    this.callbacks.onMetrics = callback;
    return this;
  }

  onComplete(callback: (message: FilteredMessage, raw: CompleteResponse) => void): this {
    this.callbacks.onComplete = callback;
    return this;
  }

  onPong(callback: (message: FilteredMessage, raw: PongResponse) => void): this {
    this.callbacks.onPong = callback;
    return this;
  }

  onError(callback: (message: FilteredMessage, raw: ErrorResponse) => void): this {
    this.callbacks.onError = callback;
    return this;
  }

  onAnyMessage(callback: (message: FilteredMessage, raw: WSResponse) => void): this {
    this.callbacks.onAnyMessage = callback;
    return this;
  }

  // ============================================
  // Message Parsing
  // ============================================

  parseMessage(rawData: string): WSResponse | null {
    try {
      return JSON.parse(rawData) as WSResponse;
    } catch {
      console.error("[WSMessageHandler] Failed to parse message:", rawData);
      return null;
    }
  }

  // ============================================
  // Message Filtering
  // ============================================

  filterMessage(raw: WSResponse): FilteredMessage {
    const base: FilteredMessage = {
      type: raw.type as WSMessageType,
      wsId: "ws_id" in raw ? raw.ws_id || "" : "",
      timestamp: "timestamp" in raw ? raw.timestamp || 0 : 0,
      raw,
    };

    switch (raw.type) {
      case WSMessageType.CONNECTED:
        return {
          ...base,
          content: `Connected with ws_id: ${raw.ws_id}`,
        };

      case WSMessageType.QUERY_RECEIVED:
        return {
          ...base,
          content: "Query received by server",
        };

      case WSMessageType.MESSAGE:
        return this.filterMessageResponse(base, raw as MessageResponse);

      case WSMessageType.FINAL:
        return this.filterFinalMessage(base, raw as FinalMessageResponse);

      case WSMessageType.METRICS:
        return this.filterMetricsMessage(base, raw as MetricsResponse);

      case WSMessageType.COMPLETE:
        return {
          ...base,
          content: "Response complete",
        };

      case WSMessageType.PONG:
        return {
          ...base,
          content: "Pong received",
        };

      case WSMessageType.ERROR:
        return {
          ...base,
          content: raw.data?.message || "Unknown error",
          errorCode: raw.data?.code,
        };

      default:
        return base;
    }
  }

  private filterMessageResponse(base: FilteredMessage, raw: MessageResponse): FilteredMessage {
    const role = raw.data.role;
    base.role = role;
    base.metrics = raw.data.metrics;

    switch (role) {
      case MessageRole.HUMAN:
        return {
          ...base,
          content: (raw as HumanMessageResponse).data.content,
        };

      case MessageRole.AI: {
        const aiData = (raw as AIMessageResponse).data;
        const reasoning: string[] = [];
        const functionCalls: FunctionCallContent[] = [];

        // Handle both cases: content can be a string or an array
        if (typeof aiData.content === "string") {
          return {
            ...base,
            content: aiData.content,
            agentName: aiData.agent_name,
          };
        } else if (Array.isArray(aiData.content)) {
          for (const item of aiData.content) {
            if (item.type === "reasoning") {
              for (const summary of item.summary) {
                reasoning.push(summary.text);
              }
            } else if (item.type === "function_call") {
              functionCalls.push(item);
            }
          }
        }

        return {
          ...base,
          reasoning,
          functionCalls,
          agentName: aiData.agent_name,
        };
      }

      case MessageRole.TOOL: {
        const toolData = (raw as ToolMessageResponse).data;
        return {
          ...base,
          content: toolData.content,
          toolName: toolData.tool_name,
        };
      }

      default:
        return base;
    }
  }

  private filterFinalMessage(base: FilteredMessage, raw: FinalMessageResponse): FilteredMessage {
    base.role = MessageRole.AI;
    base.metrics = raw.data.metrics;
    base.agentName = raw.data.agent_name;

    const reasoning: string[] = [];
    let finalText = "";
    let chartData: ChartConfig | undefined;

    // Handle both cases: content can be a string or an array
    if (typeof raw.data.content === "string") {
      finalText = raw.data.content;
    } else if (Array.isArray(raw.data.content)) {
      for (const item of raw.data.content) {
        if (item.type === "reasoning") {
          for (const summary of item.summary) {
            reasoning.push(summary.text);
          }
        } else if (item.type === "text") {
          finalText = item.text;
        }
      }
    }

    // Try to parse the final text as JSON and extract summary and chart_data
    let displayContent = finalText;
    try {
      const parsed = JSON.parse(finalText);
      if (parsed.summary) {
        displayContent = parsed.summary;
      }
      if (parsed.chart_data) {
        chartData = {
          type: parsed.chart_data.type,
          data: parsed.chart_data.data,
          options: parsed.chart_data.options,
        };
      }
    } catch {
      // Not JSON, use as-is
    }

    return {
      ...base,
      content: displayContent,
      reasoning,
      chartData,
    };
  }

  private filterMetricsMessage(base: FilteredMessage, raw: MetricsResponse): FilteredMessage {
    base.role = MessageRole.ASSISTANT;
    base.metrics = raw.data.metrics;

    return {
      ...base,
      content: "Session metrics",
    };
  }

  // ============================================
  // Message Storage
  // ============================================

  private storeMessage(filtered: FilteredMessage, raw: WSResponse): void {
    this.storedMessages.allMessages.push(filtered);

    switch (raw.type) {
      case WSMessageType.CONNECTED:
        this.storedMessages.connected = raw as ConnectedResponse;
        break;

      case WSMessageType.QUERY_RECEIVED:
        this.storedMessages.queryReceived.push(raw as QueryReceivedResponse);
        break;

      case WSMessageType.MESSAGE: {
        const msgResponse = raw as MessageResponse;
        if (msgResponse.data.role === MessageRole.HUMAN) {
          this.storedMessages.humanMessages.push(filtered);
        } else if (msgResponse.data.role === MessageRole.AI) {
          this.storedMessages.aiMessages.push(filtered);
        } else if (msgResponse.data.role === MessageRole.TOOL) {
          this.storedMessages.toolMessages.push(filtered);
        }
        break;
      }

      case WSMessageType.FINAL:
        this.storedMessages.finalMessage = filtered;
        break;

      case WSMessageType.METRICS:
        this.storedMessages.metricsMessage = filtered;
        break;

      case WSMessageType.COMPLETE:
        this.storedMessages.complete = raw as CompleteResponse;
        break;

      case WSMessageType.ERROR:
        this.storedMessages.errors.push(filtered);
        break;
    }
  }

  // ============================================
  // Main Handler Method
  // ============================================

  handleMessage(rawData: string): FilteredMessage | null {
    const parsed = this.parseMessage(rawData);
    if (!parsed) return null;

    const filtered = this.filterMessage(parsed);

    // Store the message
    this.storeMessage(filtered, parsed);

    // Call appropriate callbacks
    this.callbacks.onAnyMessage?.(filtered, parsed);

    switch (parsed.type) {
      case WSMessageType.CONNECTED:
        this.callbacks.onConnected?.(filtered, parsed as ConnectedResponse);
        break;

      case WSMessageType.QUERY_RECEIVED:
        this.callbacks.onQueryReceived?.(filtered, parsed as QueryReceivedResponse);
        break;

      case WSMessageType.MESSAGE: {
        const msgResponse = parsed as MessageResponse;
        if (msgResponse.data.role === MessageRole.HUMAN) {
          this.callbacks.onHumanMessage?.(filtered, msgResponse as HumanMessageResponse);
        } else if (msgResponse.data.role === MessageRole.AI) {
          this.callbacks.onAIMessage?.(filtered, msgResponse as AIMessageResponse);
        } else if (msgResponse.data.role === MessageRole.TOOL) {
          this.callbacks.onToolMessage?.(filtered, msgResponse as ToolMessageResponse);
        }
        break;
      }

      case WSMessageType.FINAL:
        this.callbacks.onFinalMessage?.(filtered, parsed as FinalMessageResponse);
        break;

      case WSMessageType.METRICS:
        this.callbacks.onMetrics?.(filtered, parsed as MetricsResponse);
        break;

      case WSMessageType.COMPLETE:
        this.callbacks.onComplete?.(filtered, parsed as CompleteResponse);
        break;

      case WSMessageType.PONG:
        this.callbacks.onPong?.(filtered, parsed as PongResponse);
        break;

      case WSMessageType.ERROR:
        this.callbacks.onError?.(filtered, parsed as ErrorResponse);
        break;
    }

    return filtered;
  }

  // ============================================
  // Static Type Guard Methods
  // ============================================

  static isConnected(msg: WSResponse): msg is ConnectedResponse {
    return msg.type === WSMessageType.CONNECTED;
  }

  static isQueryReceived(msg: WSResponse): msg is QueryReceivedResponse {
    return msg.type === WSMessageType.QUERY_RECEIVED;
  }

  static isMessage(msg: WSResponse): msg is MessageResponse {
    return msg.type === WSMessageType.MESSAGE;
  }

  static isFinal(msg: WSResponse): msg is FinalMessageResponse {
    return msg.type === WSMessageType.FINAL;
  }

  static isMetrics(msg: WSResponse): msg is MetricsResponse {
    return msg.type === WSMessageType.METRICS;
  }

  static isComplete(msg: WSResponse): msg is CompleteResponse {
    return msg.type === WSMessageType.COMPLETE;
  }

  static isPong(msg: WSResponse): msg is PongResponse {
    return msg.type === WSMessageType.PONG;
  }

  static isError(msg: WSResponse): msg is ErrorResponse {
    return msg.type === WSMessageType.ERROR;
  }

  static isHumanMessage(msg: WSResponse): msg is HumanMessageResponse {
    return msg.type === WSMessageType.MESSAGE && (msg as MessageResponse).data.role === MessageRole.HUMAN;
  }

  static isAIMessage(msg: WSResponse): msg is AIMessageResponse {
    return msg.type === WSMessageType.MESSAGE && (msg as MessageResponse).data.role === MessageRole.AI;
  }

  static isToolMessage(msg: WSResponse): msg is ToolMessageResponse {
    return msg.type === WSMessageType.MESSAGE && (msg as MessageResponse).data.role === MessageRole.TOOL;
  }
}

// ============================================
// Factory Function
// ============================================

export const createMessageHandler = (callbacks?: MessageHandlerCallbacks) => {
  return new WebSocketMessageHandler(callbacks);
};
