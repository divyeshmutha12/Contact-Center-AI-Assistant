"use client";

import React from "react";
import { useFlaskChat } from "@/providers/FlaskChat";
import { ChatWindow } from "./ChatWindow";
import { LoginForm } from "./LoginForm";

export function FlaskChatApp() {
  const { auth } = useFlaskChat();

  if (!auth.isAuthenticated) {
    return <LoginForm />;
  }

  return <ChatWindow />;
}

export { ChatWindow } from "./ChatWindow";
export { LoginForm } from "./LoginForm";
