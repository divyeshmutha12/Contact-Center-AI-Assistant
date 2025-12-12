"use client";

import { useRef, useEffect, useCallback, useState } from "react";
import { Message, Conversation, ThinkingStep, useChatStore } from "@/lib/store";
import { ChartConfig, ReportPath } from "@/lib/websocket-message-handler";
import { ThoughtProcess } from "./ThoughtProcess";
import { ChartRenderer } from "./ChartRenderer";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { ResponseActions } from "./ResponseActions";

const suggestedPrompts = [
  "Generate incoming call report for today",
  "Show me total calls by agent for yesterday",
  "Generate outgoing call report for this week",
  "How many missed calls were there today?",
];

// Threshold in pixels - if user is within this distance from bottom, auto-scroll
const SCROLL_THRESHOLD = 150;

// Old inventory/ocp prompts - commented out
// const suggestedPromptsOld = [
//   "Show me count of all the nodes in inventory",
//   "List all the total pods in openshift-apiserver namespace in staging cluster",
//   "Find niam ID, license and circle from PCCSM node in inventory where circle id is not null in table",
//   "Show resource usage (cpu) of all the pods in ccaas-ns namespace in staging cluster with chart.",
// ];

interface MessageListProps {
  currentConversation: Conversation | null;
  streamingContent: string;
  isLoading: boolean;
  thinkingSteps: ThinkingStep[];
  chartData: ChartConfig | null;
  reportPath: ReportPath | null;
  onSendMessage: (message: string) => void;
}

export function MessageList({
  currentConversation,
  streamingContent,
  isLoading,
  thinkingSteps,
  chartData,
  reportPath,
  onSendMessage,
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const { retryQuery, setMessageVersion, retryingMessageId } = useChatStore();

  // Track if user has manually scrolled up (away from bottom)
  const [userScrolledUp, setUserScrolledUp] = useState(false);
  const lastMessageCountRef = useRef(0);

  // Check if scroll position is near bottom
  const isNearBottom = useCallback(() => {
    const container = containerRef.current;
    if (!container) return true;

    const scrollableParent = container.closest('.overflow-y-auto');
    if (!scrollableParent) return true;

    const { scrollTop, scrollHeight, clientHeight } = scrollableParent;
    return scrollHeight - scrollTop - clientHeight < SCROLL_THRESHOLD;
  }, []);

  // Handle scroll events to detect if user scrolled up
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const scrollableParent = container.closest('.overflow-y-auto');
    if (!scrollableParent) return;

    const handleScroll = () => {
      const nearBottom = isNearBottom();
      // If user scrolls up during streaming, mark as scrolled up
      if (!nearBottom && streamingContent) {
        setUserScrolledUp(true);
      }
      // If user scrolls back to bottom, reset the flag
      if (nearBottom) {
        setUserScrolledUp(false);
      }
    };

    scrollableParent.addEventListener('scroll', handleScroll, { passive: true });
    return () => scrollableParent.removeEventListener('scroll', handleScroll);
  }, [isNearBottom, streamingContent]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // Reset userScrolledUp when a new message is sent (new user message added)
  useEffect(() => {
    const messageCount = currentConversation?.messages.length || 0;
    if (messageCount > lastMessageCountRef.current) {
      const lastMessage = currentConversation?.messages[messageCount - 1];
      // If a new user message was just added, reset scroll state and scroll to bottom
      if (lastMessage?.role === 'user') {
        setUserScrolledUp(false);
        scrollToBottom();
      }
    }
    lastMessageCountRef.current = messageCount;
  }, [currentConversation?.messages, scrollToBottom]);

  // Smart scroll: only auto-scroll if user hasn't scrolled up
  useEffect(() => {
    // Don't auto-scroll if user has manually scrolled up
    if (userScrolledUp) return;

    // Only auto-scroll if near bottom
    if (isNearBottom()) {
      scrollToBottom();
    }
  }, [streamingContent, thinkingSteps, userScrolledUp, isNearBottom, scrollToBottom]);

  const hasMessages = currentConversation && currentConversation.messages.length > 0;

  if (!hasMessages) {
    return <WelcomeScreen onSendMessage={onSendMessage} />;
  }

  // Separate messages: if we have thinking steps for the CURRENT query (isLoading or streaming),
  // hold the last assistant message to show after thought process
  const messages = currentConversation.messages;
  const lastMessage = messages[messages.length - 1];
  // Show current thinking context when loading OR when we have thinking steps with streaming content
  const hasCurrentThinkingContext = thinkingSteps.length > 0 && (isLoading || streamingContent);
  const lastIsAssistant = lastMessage?.role === "assistant";

  // Messages to show in the regular loop (exclude last assistant only if we have CURRENT thinking steps)
  const regularMessages = hasCurrentThinkingContext && lastIsAssistant
    ? messages.slice(0, -1)
    : messages;

  // The assistant response to show below thought process (only for current query)
  const assistantResponseBelowThinking = hasCurrentThinkingContext && lastIsAssistant ? lastMessage : null;

  // Helper to find the user message before an assistant message (returns both content and id)
  const findPreviousUserMessage = (messageIndex: number): { content: string; id: string } | null => {
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages[i].role === "user") {
        return { content: messages[i].content, id: messages[i].id };
      }
    }
    return null;
  };

  // Get the last user message (for retry on the latest response)
  const lastUserMsg = messages.filter(m => m.role === "user").pop();
  const lastUserMessage = lastUserMsg ? { content: lastUserMsg.content, id: lastUserMsg.id } : null;

  // Helper to handle retry
  const handleRetry = (userMessageId: string, assistantMessageId: string, query: string) => {
    retryQuery(userMessageId, assistantMessageId, query);
  };

  // Helper to handle version navigation
  const handleVersionChange = (messageId: string, newIndex: number) => {
    setMessageVersion(messageId, newIndex);
  };

  return (
    <div ref={containerRef} className="max-w-5xl mx-auto py-6 px-8">
      {regularMessages.map((message) => {
        const prevUserMsg = message.role === "assistant"
          ? findPreviousUserMessage(messages.indexOf(message))
          : null;

        // If this message is being retried, show loading instead of the message
        const isBeingRetried = message.id === retryingMessageId;

        if (isBeingRetried) {
          return <LoadingIndicator key={message.id} />;
        }

        return (
          <MessageBubble
            key={message.id}
            message={message}
            showStoredData={message.role === "assistant"}
            onRetry={prevUserMsg ? () => handleRetry(prevUserMsg.id, message.id, prevUserMsg.content) : undefined}
            onVersionChange={(newIndex: number) => handleVersionChange(message.id, newIndex)}
          />
        );
      })}

      {/* Loading indicator - only show if no thinking steps yet and not retrying (retry shows its own loading) */}
      {isLoading && !streamingContent && thinkingSteps.length === 0 && !retryingMessageId && <LoadingIndicator />}

      {/* Thought Process - show when loading or has steps for CURRENT query, but not for completed retry */}
      {hasCurrentThinkingContext && (
        <ThoughtProcess steps={thinkingSteps} isLoading={isLoading && !streamingContent} />
      )}

      {/* Streaming content (final response) - appears below thought process */}
      {streamingContent && (
        <div className="mb-6">
          <div className="w-full px-4 py-3 rounded-2xl bg-gray-100 text-gray-900">
            <MarkdownRenderer content={streamingContent} className="text-sm" reportPath={reportPath} />
          </div>
        </div>
      )}

      {/* Completed assistant response below thought process (when streaming is done) */}
      {assistantResponseBelowThinking && !streamingContent && assistantResponseBelowThinking.id !== retryingMessageId && (
        <MessageBubble
          key={assistantResponseBelowThinking.id}
          message={assistantResponseBelowThinking}
          hideActions={!!chartData}
          fullWidth={true}
          onRetry={lastUserMessage ? () => handleRetry(lastUserMessage.id, assistantResponseBelowThinking.id, lastUserMessage.content) : undefined}
          onVersionChange={(newIndex: number) => handleVersionChange(assistantResponseBelowThinking.id, newIndex)}
        />
      )}

      {/* Chart - render if chart data is available for CURRENT query (always below summary), but not during retry */}
      {chartData && assistantResponseBelowThinking && assistantResponseBelowThinking.id !== retryingMessageId && (
        <div className="mb-6">
          <ChartRenderer chartConfig={chartData} className="max-w-full" />
        </div>
      )}

      {/* Action buttons after chart (part of complete response), but not during retry */}
      {chartData && assistantResponseBelowThinking && !streamingContent && assistantResponseBelowThinking.id !== retryingMessageId && (
        <ResponseActions
          content={assistantResponseBelowThinking.content}
          onRetry={lastUserMessage ? () => handleRetry(lastUserMessage.id, assistantResponseBelowThinking.id, lastUserMessage.content) : undefined}
          totalVersions={assistantResponseBelowThinking.responseVersions?.length || 1}
          currentVersion={(assistantResponseBelowThinking.currentVersionIndex ?? 0) + 1}
          onPrevVersion={() => handleVersionChange(assistantResponseBelowThinking.id, (assistantResponseBelowThinking.currentVersionIndex ?? 0) - 1)}
          onNextVersion={() => handleVersionChange(assistantResponseBelowThinking.id, (assistantResponseBelowThinking.currentVersionIndex ?? 0) + 1)}
        />
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}

interface WelcomeScreenProps {
  onSendMessage: (message: string) => void;
}

function WelcomeScreen({ onSendMessage }: WelcomeScreenProps) {
  return (
    <div className="h-full flex flex-col items-center justify-center px-6">
      <div className="max-w-4xl w-full text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Hello Azalians!</h2>
        <p className="text-gray-500 mb-12">How can I help you today?</p>

        {/* Suggested Prompts */}
        <div className="grid grid-cols-2 gap-3 mb-8">
          {suggestedPrompts.map((prompt, index) => (
            <button
              key={index}
              onClick={() => onSendMessage(prompt)}
              className="px-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition text-left"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

interface MessageBubbleProps {
  message: Message;
  hideActions?: boolean;
  fullWidth?: boolean;
  showStoredData?: boolean; // Show thinking steps and chart from responseVersions
  onRetry?: () => void;
  onVersionChange?: (newIndex: number) => void;
}

function MessageBubble({ message, hideActions = false, fullWidth = false, showStoredData = false, onRetry, onVersionChange }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const totalVersions = message.responseVersions?.length || 1;
  const currentVersionIndex = message.currentVersionIndex ?? 0;

  // Get stored thinking steps, chart data, and report path from current version
  const currentVersion = message.responseVersions?.[currentVersionIndex];
  const storedThinkingSteps = currentVersion?.thinkingSteps || [];
  const storedChartData = currentVersion?.chartData || null;
  const storedReportPath = currentVersion?.reportPath || null;
  const hasStoredThinkingSteps = showStoredData && storedThinkingSteps.length > 0;
  const hasStoredChart = showStoredData && storedChartData;

  // Format timestamp as HH:MM
  const formatTime = (date: Date) => {
    const d = new Date(date);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
  };

  return (
    <div className={`mb-6 ${isUser ? "text-right" : ""}`}>
      {/* Thought Process for historical messages */}
      {!isUser && hasStoredThinkingSteps && (
        <ThoughtProcess steps={storedThinkingSteps} isLoading={false} />
      )}

      <div
        className={`inline-block px-4 py-3 rounded-2xl ${
          isUser
            ? "max-w-[85%] bg-black text-white"
            : fullWidth || hasStoredChart
              ? "w-full bg-gray-100 text-gray-900"
              : "max-w-[85%] bg-gray-100 text-gray-900"
        }`}
      >
        {isUser ? (
          <>
            <p className="text-sm whitespace-pre-wrap text-left">{message.content}</p>
            <p className="text-xs text-gray-300 mt-1">{formatTime(message.timestamp)}</p>
          </>
        ) : (
          <>
            <MarkdownRenderer content={message.content} className="text-sm" reportPath={storedReportPath} />
            <p className="text-xs text-gray-500 mt-1">{formatTime(message.timestamp)}</p>
          </>
        )}
      </div>

      {/* Chart for historical messages */}
      {!isUser && hasStoredChart && (
        <div className="mt-4 mb-2">
          <ChartRenderer chartConfig={storedChartData} className="max-w-full" />
        </div>
      )}

      {/* Action buttons for assistant messages */}
      {!isUser && !hideActions && (
        <ResponseActions
          content={message.content}
          onRetry={onRetry}
          totalVersions={totalVersions}
          currentVersion={currentVersionIndex + 1}
          onPrevVersion={onVersionChange ? () => onVersionChange(currentVersionIndex - 1) : undefined}
          onNextVersion={onVersionChange ? () => onVersionChange(currentVersionIndex + 1) : undefined}
        />
      )}
    </div>
  );
}

const loadingMessages = [
  "Thinking...",
  "Analyzing your request...",
  "Processing...",
  "Working on it...",
  "Almost there...",
  "Taking a bit longer, grab some coffee...",
  "Still working, hang tight...",
];

function LoadingIndicator() {
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % loadingMessages.length);
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="mb-6">
      <div className="inline-block bg-gray-100 px-4 py-3 rounded-2xl">
        <div className="flex items-center gap-2">
          <LoadingSpinner />
          <span className="text-sm text-gray-600">{loadingMessages[messageIndex]}</span>
        </div>
      </div>
    </div>
  );
}

function LoadingSpinner() {
  return (
    <svg
      className="w-4 h-4 text-gray-500 animate-spin"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}
