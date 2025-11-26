"use client";

import { FlaskChatProvider } from "@/providers/FlaskChat";
import { FlaskChatApp } from "@/components/flask-chat";
import { Toaster } from "@/components/ui/sonner";
import React from "react";

export default function HomePage(): React.ReactNode {
  return (
    <React.Suspense fallback={<div>Loading...</div>}>
      <Toaster />
      <FlaskChatProvider>
        <FlaskChatApp />
      </FlaskChatProvider>
    </React.Suspense>
  );
}
