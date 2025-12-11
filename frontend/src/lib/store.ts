/**
 * Store Barrel Export
 *
 * This file re-exports all store-related modules for convenient importing.
 * The stores have been split into separate files for better maintainability:
 *
 * - types.ts: All TypeScript interfaces (User, Message, Conversation, etc.)
 * - auth-store.ts: Authentication state and actions (useAuthStore)
 * - chat-store.ts: Chat/WebSocket state and actions (useChatStore)
 * - chat-store-helpers.ts: Helper functions for chat store (message creation, WS event handling)
 */

// Re-export all types
export type {
  User,
  AuthTokens,
  LoginResponse,
  ThinkingStep,
  ResponseVersion,
  Message,
  Conversation,
} from "./types";

// Re-export auth store
export { useAuthStore } from "./auth-store";

// Re-export chat store
export { useChatStore } from "./chat-store";

// Re-export chat store helper utilities (if needed externally)
export {
  createThinkingStep,
  createResponseVersion,
  createAssistantMessage,
  createErrorMessage,
} from "./chat-store-helpers";
