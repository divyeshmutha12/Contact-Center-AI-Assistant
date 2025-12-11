"use client";

import { useState } from "react";

interface ResponseActionsProps {
  content: string;
  onFeedback?: (type: "positive" | "negative") => void;
  onRetry?: () => void;
  // Version navigation props
  totalVersions?: number;
  currentVersion?: number;
  onPrevVersion?: () => void;
  onNextVersion?: () => void;
}

export function ResponseActions({
  content,
  onFeedback,
  onRetry,
  totalVersions = 1,
  currentVersion = 1,
  onPrevVersion,
  onNextVersion,
}: ResponseActionsProps) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<"positive" | "negative" | null>(null);
  const hasMultipleVersions = totalVersions > 1;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const handleFeedback = (type: "positive" | "negative") => {
    setFeedback(type);
    onFeedback?.(type);
  };

  return (
    <div className="flex items-center gap-1 mt-2">
      {/* Copy button */}
      <button
        onClick={handleCopy}
        className="p-1.5 rounded-md hover:bg-gray-200 transition-colors group"
        title={copied ? "Copied!" : "Copy to clipboard"}
      >
        {copied ? (
          <CheckIcon className="w-4 h-4 text-green-600" />
        ) : (
          <CopyIcon className="w-4 h-4 text-gray-400 group-hover:text-gray-600" />
        )}
      </button>

      {/* Positive feedback */}
      <button
        onClick={() => handleFeedback("positive")}
        className={`p-1.5 rounded-md hover:bg-gray-200 transition-colors group ${
          feedback === "positive" ? "bg-gray-200" : ""
        }`}
        title="Good response"
      >
        <ThumbsUpIcon
          className={`w-4 h-4 ${
            feedback === "positive"
              ? "text-green-600"
              : "text-gray-400 group-hover:text-gray-600"
          }`}
        />
      </button>

      {/* Negative feedback */}
      <button
        onClick={() => handleFeedback("negative")}
        className={`p-1.5 rounded-md hover:bg-gray-200 transition-colors group ${
          feedback === "negative" ? "bg-gray-200" : ""
        }`}
        title="Bad response"
      >
        <ThumbsDownIcon
          className={`w-4 h-4 ${
            feedback === "negative"
              ? "text-red-600"
              : "text-gray-400 group-hover:text-gray-600"
          }`}
        />
      </button>

      {/* Retry button */}
      {onRetry && (
        <button
          onClick={onRetry}
          className="p-1.5 rounded-md hover:bg-gray-200 transition-colors group"
          title="Retry this query"
        >
          <RetryIcon className="w-4 h-4 text-gray-400 group-hover:text-gray-600" />
        </button>
      )}

      {/* Version navigation - only show when multiple versions exist */}
      {hasMultipleVersions && (
        <div className="flex items-center gap-1 ml-2 border-l border-gray-200 pl-2">
          <button
            onClick={onPrevVersion}
            disabled={currentVersion <= 1}
            className="p-1 rounded hover:bg-gray-200 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            title="Previous version"
          >
            <ChevronLeftIcon className="w-4 h-4 text-gray-500" />
          </button>
          <span className="text-xs text-gray-500 min-w-8 text-center">
            {currentVersion} / {totalVersions}
          </span>
          <button
            onClick={onNextVersion}
            disabled={currentVersion >= totalVersions}
            className="p-1 rounded hover:bg-gray-200 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            title="Next version"
          >
            <ChevronRightIcon className="w-4 h-4 text-gray-500" />
          </button>
        </div>
      )}
    </div>
  );
}

function CopyIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
      />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M5 13l4 4L19 7"
      />
    </svg>
  );
}

function ThumbsUpIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"
      />
    </svg>
  );
}

function ThumbsDownIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5"
      />
    </svg>
  );
}

function RetryIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
      />
    </svg>
  );
}

function ChevronLeftIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 19l-7-7 7-7"
      />
    </svg>
  );
}

function ChevronRightIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 5l7 7-7 7"
      />
    </svg>
  );
}
