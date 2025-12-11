"use client";

import { useState } from "react";
import Image from "next/image";
import { useAuthStore, useChatStore, Conversation } from "@/lib/store";

interface SidebarProps {
  onLogout: () => void;
}

export function Sidebar({ onLogout }: SidebarProps) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { user } = useAuthStore();
  const {
    isConnected,
    conversations,
    currentConversation,
    setCurrentConversation,
    deleteConversation,
    clearStreamingContent,
  } = useChatStore();

  const createNewConversation = () => {
    setCurrentConversation(null);
    clearStreamingContent();
  };

  const handleDeleteConversation = (id: string) => {
    deleteConversation(id);
  };

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div
      className={`border-r border-gray-200 flex flex-col bg-white transition-all duration-300 ${
        isCollapsed ? "w-16" : "w-60"
      }`}
    >
      {/* Sidebar Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className={`flex items-center gap-2 ${isCollapsed ? "justify-center w-full" : ""}`}>
            {/* Toggle Sidebar Button */}
            <button
              onClick={toggleSidebar}
              className="p-1.5 hover:bg-gray-100 rounded-lg transition"
              title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              <SidebarToggleIcon isCollapsed={isCollapsed} />
            </button>
            {!isCollapsed && (
              <>
                <Image
                  src="/azalio_logo.png"
                  alt="Azalio"
                  width={24}
                  height={24}
                  style={{ width: 'auto', height: 'auto' }}
                />
                <h1 className="text-lg font-semibold">Azalio</h1>
              </>
            )}
          </div>
          {!isCollapsed && (
            <div className="flex items-center gap-2">
              <button
                onClick={() =>
                  handleDeleteConversation(currentConversation?.id || "")
                }
                className="p-1.5 hover:bg-gray-100 rounded-lg transition"
                title="Delete conversation"
              >
                <svg
                  className="w-5 h-5 text-gray-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
              <button
                onClick={createNewConversation}
                className="p-1.5 hover:bg-gray-100 rounded-lg transition"
                title="New conversation"
              >
                <svg
                  className="w-5 h-5 text-gray-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Collapsed: Show icon buttons only */}
      {isCollapsed ? (
        <div className="flex-1 flex flex-col items-center py-4 gap-2">
          <button
            onClick={createNewConversation}
            className="p-2 hover:bg-gray-100 rounded-lg transition"
            title="New conversation"
          >
            <svg
              className="w-5 h-5 text-gray-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
          </button>
          <button
            onClick={() =>
              handleDeleteConversation(currentConversation?.id || "")
            }
            className="p-2 hover:bg-gray-100 rounded-lg transition"
            title="Delete conversation"
          >
            <svg
              className="w-5 h-5 text-gray-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        </div>
      ) : (
        <>
          {/* Conversations List */}
          <ConversationList
            conversations={conversations}
            currentConversation={currentConversation}
            onSelect={setCurrentConversation}
          />
        </>
      )}

      {/* Connection Status */}
      <ConnectionStatus isConnected={isConnected} isCollapsed={isCollapsed} />

      {/* User Section */}
      <UserSection
        user={user}
        showMenu={showUserMenu}
        onToggleMenu={() => setShowUserMenu(!showUserMenu)}
        onLogout={onLogout}
        isCollapsed={isCollapsed}
      />
    </div>
  );
}

interface ConversationListProps {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  onSelect: (conversation: Conversation) => void;
}

function ConversationList({
  conversations,
  currentConversation,
  onSelect,
}: ConversationListProps) {
  return (
    <div className="flex-1 overflow-y-auto p-2">
      {conversations.length === 0 ? (
        <p className="text-sm text-gray-500 px-2 py-4">
          Your conversations will appear here once you start chatting!
        </p>
      ) : (
        <div className="space-y-1">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => onSelect(conv)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm truncate transition ${
                currentConversation?.id === conv.id
                  ? "bg-gray-100 text-black"
                  : "text-gray-600 hover:bg-gray-50"
              }`}
            >
              {conv.title}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

interface ConnectionStatusProps {
  isConnected: boolean;
  isCollapsed: boolean;
}

function ConnectionStatus({ isConnected, isCollapsed }: ConnectionStatusProps) {
  return (
    <div className={`py-2 border-t border-gray-100 ${isCollapsed ? "px-2 flex justify-center" : "px-4"}`}>
      <div className="flex items-center gap-2" title={isConnected ? "Connected" : "Disconnected"}>
        <div
          className={`w-2 h-2 rounded-full ${
            isConnected ? "bg-green-500" : "bg-gray-300"
          }`}
        />
        {!isCollapsed && (
          <span className="text-xs text-gray-500">
            {isConnected ? "Connected" : "Disconnected"}
          </span>
        )}
      </div>
    </div>
  );
}

interface UserSectionProps {
  user: { full_name?: string | null; username?: string } | null;
  showMenu: boolean;
  onToggleMenu: () => void;
  onLogout: () => void;
  isCollapsed: boolean;
}

function UserSection({ user, showMenu, onToggleMenu, onLogout, isCollapsed }: UserSectionProps) {
  const userInitial = (user?.full_name || user?.username || "G")[0]?.toUpperCase();
  const userName = user?.full_name || user?.username || "Guest";

  return (
    <div className="border-t border-gray-200 p-2">
      <div className="relative">
        <button
          onClick={onToggleMenu}
          className={`w-full flex items-center gap-3 py-2 hover:bg-gray-50 rounded-lg transition ${
            isCollapsed ? "justify-center px-0" : "px-3"
          }`}
          title={isCollapsed ? userName : undefined}
        >
          <div className="w-8 h-8 rounded-full bg-linear-to-br from-orange-400 to-pink-500 flex items-center justify-center text-white text-sm font-medium shrink-0">
            {userInitial}
          </div>
          {!isCollapsed && (
            <>
              <span className="text-sm font-medium text-gray-700 flex-1 text-left truncate">
                {userName}
              </span>
              <svg
                className={`w-4 h-4 text-gray-400 transition-transform ${
                  showMenu ? "rotate-180" : ""
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 15l7-7 7 7"
                />
              </svg>
            </>
          )}
        </button>
        {showMenu && (
          <div className={`absolute bottom-full mb-1 bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden ${
            isCollapsed ? "left-full ml-1 w-32" : "left-0 w-full"
          }`}>
            <button
              onClick={onLogout}
              className="w-full px-4 py-2 text-sm text-left text-red-600 hover:bg-gray-50 transition"
            >
              Sign out
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// Sidebar toggle icon - shows different icons based on collapsed state
function SidebarToggleIcon({ isCollapsed }: { isCollapsed: boolean }) {
  if (isCollapsed) {
    // Arrow pointing right (expand)
    return (
      <svg
        className="w-5 h-5 text-gray-500"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13 5l7 7-7 7M5 5l7 7-7 7"
        />
      </svg>
    );
  }
  // Sidebar with arrow pointing left (collapse)
  return (
    <svg
      className="w-5 h-5 text-gray-500"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M11 19l-7-7 7-7M19 19l-7-7 7-7"
      />
    </svg>
  );
}
