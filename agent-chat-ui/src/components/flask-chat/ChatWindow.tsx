"use client";

import React, { useState, useRef, useEffect } from "react";
import Image from "next/image";
import { useFlaskChat } from "@/providers/FlaskChat";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  Send,
  LogOut,
  Trash2,
  Loader2,
  AlertCircle,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  MessageSquare,
  Copy,
  Check,
} from "lucide-react";
import { MarkdownText } from "@/components/thread/markdown-text";

// App name - change this to customize
const APP_NAME = "Azalio Agent";

export function ChatWindow() {
  const {
    auth,
    logout,
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
  } = useFlaskChat();

  const [input, setInput] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Copy message to clipboard
  const handleCopyMessage = async (messageId: string, content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const message = input;
    setInput("");
    await sendMessage(message);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar */}
      <div
        className={cn(
          "flex flex-col border-r bg-white transition-all duration-300 ease-in-out",
          sidebarOpen ? "w-72" : "w-0 overflow-hidden"
        )}
      >
        {/* Sidebar Header */}
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarOpen(false)}
              className="h-8 w-8 p-0"
            >
              <PanelLeftClose className="h-5 w-5" />
            </Button>
            <span className="font-semibold text-gray-700">Chat History</span>
          </div>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <Button
            variant="outline"
            className="w-full justify-start gap-2"
            onClick={clearMessages}
          >
            <Plus className="h-4 w-4" />
            New Chat
          </Button>
        </div>

        {/* Chat History List */}
        <div className="flex-1 overflow-y-auto px-3">
          {messages.length > 0 && (
            <div className="space-y-1">
              <div className="flex items-center gap-2 rounded-lg bg-blue-50 px-3 py-2 text-sm text-blue-700">
                <MessageSquare className="h-4 w-4" />
                <span className="truncate">Current conversation</span>
              </div>
            </div>
          )}
          {messages.length === 0 && (
            <p className="py-4 text-center text-sm text-gray-400">
              No chat history yet
            </p>
          )}
        </div>

        {/* Sidebar Footer - User Info */}
        <div className="border-t p-3">
          <div className="flex items-center gap-3 rounded-lg bg-gray-50 px-3 py-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#2563eb] text-white font-semibold text-sm">
              {auth.username ? auth.username.charAt(0).toUpperCase() : "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="truncate text-sm font-medium text-gray-700">
                {auth.username}
              </p>
              <p className="text-xs text-gray-400">Logged in</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex flex-1 flex-col">
        {/* Header */}
        <header className="flex items-center justify-between border-b bg-white px-4 py-3 shadow-sm">
          <div className="flex items-center gap-3">
            {!sidebarOpen && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSidebarOpen(true)}
                className="h-8 w-8 p-0"
              >
                <PanelLeftOpen className="h-5 w-5" />
              </Button>
            )}
            <Image
              src="/azalio_logo.png"
              alt={APP_NAME}
              width={40}
              height={40}
              className="object-contain"
            />
            <div>
              <h1 className="text-lg font-semibold text-[#2563eb]">{APP_NAME}</h1>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={clearMessages}
              disabled={messages.length === 0}
              title="Clear chat"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={logout}
              className="text-red-600 hover:bg-red-50 hover:text-red-700"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </Button>
          </div>
        </header>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="mx-auto max-w-3xl space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="mb-4">
                  <Image
                    src="/azalio_logo.png"
                    alt={APP_NAME}
                    width={80}
                    height={80}
                    className="object-contain"
                  />
                </div>
                <h2 className="mb-2 text-xl font-semibold text-[#2563eb]">
                  Welcome to Azalio Agent
                </h2>
                <p className="max-w-md text-gray-500">
                  Ask questions about your data using natural
                  language. For example:
                </p>
                <div className="mt-4 space-y-2 text-sm text-gray-600">
                  <p className="rounded-lg bg-white px-4 py-2 shadow-sm border cursor-pointer hover:bg-gray-50 transition-colors">
                    "How many calls were made yesterday?"
                  </p>
                  <p className="rounded-lg bg-white px-4 py-2 shadow-sm border cursor-pointer hover:bg-gray-50 transition-colors">
                    "Show customers from New York"
                  </p>
                  <p className="rounded-lg bg-white px-4 py-2 shadow-sm border cursor-pointer hover:bg-gray-50 transition-colors">
                    "What's the average call duration?"
                  </p>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "flex gap-3 group",
                    message.role === "user" ? "justify-end" : "justify-start"
                  )}
                >
                  {message.role === "assistant" && (
                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-white border shadow-sm overflow-hidden">
                      <Image
                        src="/azalio_logo.png"
                        alt="AI"
                        width={24}
                        height={24}
                        className="object-contain"
                      />
                    </div>
                  )}

                  <div
                    className={cn(
                      "flex flex-col max-w-[80%]",
                      message.role === "user" ? "items-end" : "items-start"
                    )}
                  >
                    <div
                      className={cn(
                        "rounded-2xl px-4 py-3",
                        message.role === "user"
                          ? "bg-[#2563eb] text-white shadow-sm"
                          : "bg-white shadow-sm border"
                      )}
                    >
                      {message.role === "assistant" ? (
                        <div className="prose prose-sm max-w-none">
                          <MarkdownText>{message.content}</MarkdownText>
                        </div>
                      ) : (
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      )}
                      <p
                        className={cn(
                          "mt-1 text-xs",
                          message.role === "user"
                            ? "text-blue-200"
                            : "text-gray-400"
                        )}
                      >
                        {message.timestamp.toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                    {/* Copy button */}
                    <button
                      onClick={() => handleCopyMessage(message.id, message.content)}
                      className={cn(
                        "flex items-center gap-1 px-2 py-1 mt-1 text-xs rounded-md transition-all duration-200",
                        "opacity-0 group-hover:opacity-100",
                        copiedMessageId === message.id
                          ? "text-green-600 bg-green-50"
                          : "text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                      )}
                      title="Copy message"
                    >
                      {copiedMessageId === message.id ? (
                        <>
                          <Check className="h-3 w-3" />
                          <span>Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="h-3 w-3" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>

                  {message.role === "user" && (
                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-[#2563eb] text-white font-semibold text-sm">
                      {auth.username ? auth.username.charAt(0).toUpperCase() : "U"}
                    </div>
                  )}
                </div>
              ))
            )}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex gap-3">
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-white border shadow-sm overflow-hidden">
                  <Image
                    src="/azalio_logo.png"
                    alt="AI"
                    width={24}
                    height={24}
                    className="object-contain"
                  />
                </div>
                <div className="rounded-2xl border bg-white px-4 py-3 shadow-sm">
                  <div className="flex items-center gap-2 text-gray-500">
                    <Loader2 className="h-4 w-4 animate-spin text-[#2563eb]" />
                    <span>Thinking...</span>
                  </div>
                </div>
              </div>
            )}

            {/* Error message */}
            {error && (
              <div className="flex items-center gap-2 rounded-lg bg-red-50 px-4 py-3 text-red-700">
                <AlertCircle className="h-5 w-5" />
                <span>{error}</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t bg-white px-4 py-4">
          <form
            onSubmit={handleSubmit}
            className="mx-auto flex max-w-3xl gap-3"
          >
            <div className="relative flex-1">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message..."
                rows={1}
                className="w-full resize-none rounded-xl border border-gray-300 px-4 py-3 pr-12 focus:border-[#2563eb] focus:outline-none focus:ring-2 focus:ring-[#2563eb]/20"
                disabled={isLoading}
              />
            </div>
            <Button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="h-12 rounded-xl px-6 bg-[#2563eb] hover:bg-[#1d4ed8] text-white font-medium shadow-md hover:shadow-lg transition-all duration-200"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin mr-2" />
                  Sending...
                </>
              ) : (
                "Send"
              )}
            </Button>
          </form>
          <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-gray-400">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
}
