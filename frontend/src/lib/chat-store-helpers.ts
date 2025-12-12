import {
  WebSocketMessageHandler,
  WSMessageType,
  MessageRole,
  FilteredMessage,
  ChartConfig,
  ReportPath,
} from "./websocket-message-handler";
import { ThinkingStep, Message, ResponseVersion, Conversation } from "./types";

// ============================================
// WebSocket Handler Types
// ============================================

export interface WebSocketHandlerCallbacks {
  // State setters
  setSessionId: (wsId: string) => void;  // Named for backwards compat, but stores ws_id
  setFilteredMessages: (messages: FilteredMessage[]) => void;
  addThinkingStep: (step: ThinkingStep) => void;
  startFakeStreaming: (content: string, chartData?: ChartConfig, reportPath?: ReportPath) => void;

  // Getters for current state
  getFullResponseContent: () => string;
  getCurrentConversation: () => Conversation | null;
  isStillStreaming: () => boolean;
  getRetryingMessageId: () => string | null;
  getCurrentChartData: () => ChartConfig | null;
  getCurrentReportPath: () => ReportPath | null;
  getThinkingSteps: () => ThinkingStep[];

  // State updates
  updateConversationWithRetry: (
    conv: Conversation,
    retryingMessageId: string,
    fullResponseContent: string,
    currentChartData: ChartConfig | null,
    currentReportPath: ReportPath | null,
    thinkingSteps: ThinkingStep[]
  ) => void;
  updateConversationWithNewMessage: (
    conv: Conversation,
    fullResponseContent: string,
    currentChartData: ChartConfig | null,
    currentReportPath: ReportPath | null,
    thinkingSteps: ThinkingStep[]
  ) => void;
  setLoadingComplete: () => void;
  setError: (error: string, conv?: Conversation | null) => void;
}

// ============================================
// Create Thinking Step from Filtered Message
// ============================================

export function createThinkingStep(filtered: FilteredMessage): ThinkingStep {
  return {
    id: `thinking-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`,
    agentName: filtered.agentName || "AI",
    reasoning: filtered.reasoning || [],
    functionCalls: filtered.functionCalls?.map((fc) => ({
      name: fc.name,
      arguments: fc.arguments,
      status: fc.status,
    })) || [],
    timestamp: filtered.timestamp,
  };
}

// ============================================
// Handle WebSocket Message
// ============================================

export function handleWebSocketMessage(
  filtered: FilteredMessage,
  messageHandler: WebSocketMessageHandler,
  callbacks: WebSocketHandlerCallbacks,
  currentQueryMessages: FilteredMessage[],
  setState: (updates: Record<string, unknown>) => void
): void {
  // Store filtered messages and update current query messages
  setState({
    filteredMessages: messageHandler.getStoredMessages(),
    currentQueryMessages: [...currentQueryMessages, filtered],
  });

  switch (filtered.type) {
    case WSMessageType.CONNECTED:
      if (filtered.wsId) {
        console.log("[WS] WebSocket ID received:", filtered.wsId);
        callbacks.setSessionId(filtered.wsId);
      }
      break;

    case WSMessageType.QUERY_RECEIVED:
      console.log("[WS] Query received by server");
      break;

    case WSMessageType.STREAM:
      // Ignore stream messages - we only want the final response
      // This prevents word-by-word streaming, showing only complete response
      break;

    case WSMessageType.TOOL_START:
      console.log("[WS] Tool started:", filtered.toolName);
      break;

    case WSMessageType.TOOL_END:
      console.log("[WS] Tool ended:", filtered.toolName);
      break;

    case WSMessageType.MESSAGE:
      handleMessageType(filtered, callbacks);
      break;

    case WSMessageType.FINAL:
      console.log("[WS] Final message received, starting fake streaming");
      if (filtered.content) {
        callbacks.startFakeStreaming(filtered.content, filtered.chartData, filtered.reportPath);
      }
      break;

    case WSMessageType.METRICS:
      console.log("[WS] Metrics received:", filtered.metrics);
      break;

    case WSMessageType.COMPLETE:
      console.log("[WS] Response complete");
      handleCompleteMessage(callbacks);
      break;

    case WSMessageType.PONG:
      console.log("[WS] Pong received");
      break;

    case WSMessageType.ERROR:
      console.log("[WS] Error:", filtered.content, filtered.errorCode);
      const errorMsg = filtered.content || "Unknown error";
      callbacks.setError(errorMsg, callbacks.getCurrentConversation());
      break;

    default:
      console.log("[WS] Unknown message type:", filtered.type);
  }
}

// ============================================
// Handle MESSAGE Type
// ============================================

function handleMessageType(
  filtered: FilteredMessage,
  callbacks: WebSocketHandlerCallbacks
): void {
  if (filtered.role === MessageRole.HUMAN) {
    console.log("[WS] Human message echoed back");
  } else if (filtered.role === MessageRole.AI) {
    console.log("[WS] AI reasoning:", filtered.reasoning);
    if (filtered.reasoning && filtered.reasoning.length > 0) {
      const thinkingStep = createThinkingStep(filtered);
      callbacks.addThinkingStep(thinkingStep);
    }
  } else if (filtered.role === MessageRole.TOOL) {
    console.log("[WS] Tool result from:", filtered.toolName);
  }
}

// ============================================
// Handle COMPLETE Message
// ============================================

function handleCompleteMessage(callbacks: WebSocketHandlerCallbacks): void {
  const checkAndComplete = () => {
    const fullResponseContent = callbacks.getFullResponseContent();
    const conv = callbacks.getCurrentConversation();
    const stillStreaming = callbacks.isStillStreaming();
    const retryingMessageId = callbacks.getRetryingMessageId();
    const currentChartData = callbacks.getCurrentChartData();
    const currentReportPath = callbacks.getCurrentReportPath();
    const thinkingSteps = callbacks.getThinkingSteps();

    if (stillStreaming) {
      setTimeout(checkAndComplete, 100);
      return;
    }

    if (fullResponseContent && conv) {
      if (retryingMessageId) {
        callbacks.updateConversationWithRetry(
          conv,
          retryingMessageId,
          fullResponseContent,
          currentChartData,
          currentReportPath,
          thinkingSteps
        );
      } else {
        callbacks.updateConversationWithNewMessage(
          conv,
          fullResponseContent,
          currentChartData,
          currentReportPath,
          thinkingSteps
        );
      }
    } else {
      callbacks.setLoadingComplete();
    }
  };

  checkAndComplete();
}

// ============================================
// Create Response Version
// ============================================

export function createResponseVersion(
  content: string,
  chartData: ChartConfig | null,
  reportPath: ReportPath | null,
  thinkingSteps: ThinkingStep[],
  isOriginal: boolean = false
): ResponseVersion {
  return {
    id: isOriginal ? `version-original-${Date.now()}` : `version-${Date.now()}`,
    content,
    timestamp: new Date(),
    chartData: chartData || undefined,
    reportPath: reportPath || undefined,
    thinkingSteps: [...thinkingSteps],
  };
}

// ============================================
// Create Assistant Message
// ============================================

export function createAssistantMessage(
  content: string,
  chartData: ChartConfig | null,
  reportPath: ReportPath | null,
  thinkingSteps: ThinkingStep[]
): Message {
  const firstVersion = createResponseVersion(content, chartData, reportPath, thinkingSteps, true);

  return {
    id: (Date.now() + 1).toString(),
    content,
    role: "assistant",
    timestamp: new Date(),
    responseVersions: [firstVersion],
    currentVersionIndex: 0,
  };
}

// ============================================
// Create Error Message
// ============================================

export function createErrorMessage(errorMsg: string): Message {
  return {
    id: (Date.now() + 1).toString(),
    content: `Error: ${errorMsg}`,
    role: "assistant",
    timestamp: new Date(),
  };
}
