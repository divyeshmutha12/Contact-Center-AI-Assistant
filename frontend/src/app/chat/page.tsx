"use client";

import { useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore, useChatStore, Message, Conversation } from "@/lib/store";
import { Sidebar, ChatHeader, MessageList, ChatInput } from "@/components/chat";

export default function ChatPage() {
  const router = useRouter();
  const hasConnectedRef = useRef(false);

  // Auth store
  const { isAuthenticated, logout } = useAuthStore();

  // Chat store
  const {
    isLoading,
    isConnected,
    wsId,
    streamingContent,
    thinkingSteps,
    currentChartData,
    currentReportPath,
    currentConversation,
    connect,
    reconnect,
    sendQuery,
    setCurrentConversation,
    addConversation,
    updateConversation,
  } = useChatStore();

  // Auth check - redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, router]);

  // Initial WebSocket connection on mount
  useEffect(() => {
    if (isAuthenticated && !hasConnectedRef.current) {
      hasConnectedRef.current = true;
      // Small delay to avoid React Strict Mode double-mount issues
      const timeoutId = setTimeout(() => {
        connect();
      }, 100);
      return () => clearTimeout(timeoutId);
    }
  }, [isAuthenticated, connect]);

  // Reconnect if disconnected and we previously had a connection
  useEffect(() => {
    if (isAuthenticated && !isConnected && wsId && hasConnectedRef.current) {
      console.log("[Chat] Attempting reconnection (previous ws_id:", wsId, ")");
      reconnect();
    }
  }, [isAuthenticated, isConnected, wsId, reconnect]);

  const handleSendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return;

      if (!isAuthenticated) {
        router.push("/login");
        return;
      }

      const newMessage: Message = {
        id: Date.now().toString(),
        content: content.trim(),
        role: "user",
        timestamp: new Date(),
      };

      let conversation: Conversation;

      if (currentConversation) {
        conversation = {
          ...currentConversation,
          messages: [...currentConversation.messages, newMessage],
        };
        updateConversation(conversation);
      } else {
        // Create new conversation - memory is handled by ws_id on backend
        conversation = {
          id: Date.now().toString(),
          title: content.slice(0, 30) + (content.length > 30 ? "..." : ""),
          messages: [newMessage],
          createdAt: new Date(),
        };
        addConversation(conversation);
      }

      setCurrentConversation(conversation);

      // If not connected, reconnect first
      if (!isConnected) {
        if (wsId) {
          reconnect();
        } else {
          connect();
        }
        // Wait for connection before sending
        setTimeout(() => {
          sendQuery(content.trim());
        }, 500);
      } else {
        // Already connected, send immediately
        sendQuery(content.trim());
      }
    },
    [
      isLoading,
      isAuthenticated,
      isConnected,
      wsId,
      currentConversation,
      router,
      connect,
      reconnect,
      sendQuery,
      setCurrentConversation,
      addConversation,
      updateConversation,
    ]
  );

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  // Don't render if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-white">
      {/* Sidebar */}
      <Sidebar onLogout={handleLogout} />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <ChatHeader />

        {/* Chat Content */}
        <div className="flex-1 overflow-y-auto">
          <MessageList
            currentConversation={currentConversation}
            streamingContent={streamingContent}
            isLoading={isLoading}
            thinkingSteps={thinkingSteps}
            chartData={currentChartData}
            reportPath={currentReportPath}
            onSendMessage={handleSendMessage}
          />
        </div>

        {/* Input Area */}
        <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
}
