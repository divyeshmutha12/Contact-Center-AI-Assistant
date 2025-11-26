"use client";

import React, { useState } from "react";
import Image from "next/image";
import { useFlaskChat } from "@/providers/FlaskChat";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, AlertCircle } from "lucide-react";

// App name - change this to customize
const APP_NAME = "Azalio Agent";

export function LoginForm() {
  const { login, error } = useFlaskChat();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);

    if (!username.trim() || !password.trim()) {
      setLocalError("Please enter both username and password");
      return;
    }

    setIsLoading(true);
    const success = await login(username, password);
    setIsLoading(false);

    if (!success) {
      setLocalError(error || "Login failed. Please try again.");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="w-full max-w-md">
        <div className="rounded-2xl bg-white p-8 shadow-xl">
          {/* Logo & Title */}
          <div className="mb-8 text-center">
            <Image
              src="/azalio_logo.png"
              alt={APP_NAME}
              width={50}
              height={50}
              className="mx-auto mb-4 rounded-full"
            />
            <h1 className="text-2xl font-bold text-gray-900">
              {APP_NAME}
            </h1>
            <p className="mt-2 text-gray-500">
              Sign in to access your dashboard
            </p>
          </div>

          {/* Error Message */}
          {(localError || error) && (
            <div className="mb-6 flex items-center gap-2 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{localError || error}</span>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                disabled={isLoading}
                autoComplete="username"
                className="h-11"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                disabled={isLoading}
                autoComplete="current-password"
                className="h-11"
              />
            </div>

            <Button
              type="submit"
              className="h-11 w-full"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign In"
              )}
            </Button>
          </form>

          {/* Footer */}
          <p className="mt-6 text-center text-xs text-gray-400">
            Your AI-powered data assistant
          </p>
        </div>
      </div>
    </div>
  );
}
