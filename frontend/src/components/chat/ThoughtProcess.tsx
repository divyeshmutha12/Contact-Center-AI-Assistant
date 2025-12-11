"use client";

import { useState } from "react";
import { ThinkingStep } from "@/lib/store";

interface ThoughtProcessProps {
  steps: ThinkingStep[];
  isLoading?: boolean;
}

export function ThoughtProcess({ steps, isLoading }: ThoughtProcessProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (steps.length === 0 && !isLoading) {
    return null;
  }

  // Get a summary title from the LATEST reasoning step (so user sees current progress)
  const getSummaryTitle = (): string => {
    if (steps.length === 0) {
      return "Thinking...";
    }
    // Get the last step (most recent)
    const lastStep = steps[steps.length - 1];
    const lastReasoning = lastStep?.reasoning?.[0];
    if (lastReasoning) {
      // Extract first line or first ~60 chars
      const firstLine = lastReasoning.split("\n")[0];
      // Remove markdown bold markers
      const cleaned = firstLine.replace(/\*\*/g, "");
      if (cleaned.length > 60) {
        return cleaned.substring(0, 60) + "...";
      }
      return cleaned;
    }
    return "Processing your request...";
  };

  return (
    <div className="mb-4">
      <div className="border border-gray-200 rounded-xl overflow-hidden">
        {/* Collapsible Header */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
        >
          <div className="flex items-center gap-2">
            {isLoading && steps.length === 0 ? (
              <LoadingSpinner />
            ) : (
              <ThinkingIcon />
            )}
            <span className="text-sm text-gray-700 font-medium">
              {isLoading && steps.length === 0 ? "Thinking..." : "Thought process"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {!isExpanded && (
              <>
                {/* Show loading spinner next to heading when still loading */}
                {isLoading && steps.length > 0 && <LoadingSpinner />}
                <span className="text-sm text-gray-500 max-w-[300px] truncate hidden sm:block">
                  {getSummaryTitle()}
                </span>
              </>
            )}
            <ChevronIcon isExpanded={isExpanded} />
          </div>
        </button>

        {/* Expanded Content */}
        {isExpanded && (
          <div className="px-4 py-3 bg-white border-t border-gray-200 max-h-[400px] overflow-y-auto">
            {steps.map((step, index) => (
              <ThinkingStepItem key={step.id} step={step} isLast={index === steps.length - 1 && !isLoading} />
            ))}
            {/* Show a subtle loading indicator at the bottom when still thinking */}
            {isLoading && (
              <div className="flex items-center gap-2 text-gray-400 text-xs mt-3 pt-3 border-t border-gray-100">
                <LoadingSpinner />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

interface ThinkingStepItemProps {
  step: ThinkingStep;
  isLast: boolean;
}

function ThinkingStepItem({ step, isLast }: ThinkingStepItemProps) {
  return (
    <div className={`${!isLast ? "mb-4 pb-4 border-b border-gray-100" : ""}`}>
      {/* Agent Name Badge */}
      {step.agentName && (
        <div className="mb-2">
          <span className="inline-block px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
            {step.agentName}
          </span>
        </div>
      )}

      {/* Reasoning Text */}
      {step.reasoning.map((text, idx) => (
        <p key={idx} className="text-sm text-gray-700 mb-2 whitespace-pre-wrap leading-relaxed">
          {formatReasoningText(text)}
        </p>
      ))}

      {/* Function Calls */}
      {step.functionCalls.length > 0 && (
        <div className="mt-2 space-y-1">
          {step.functionCalls.map((fc, idx) => (
            <div
              key={idx}
              className="flex items-center gap-2 text-xs bg-gray-100 px-2 py-1 rounded"
            >
              <span className="text-gray-500">Tool:</span>
              <span className="font-mono text-gray-700">{fc.name}</span>
              {fc.status && (
                <span
                  className={`px-1.5 py-0.5 rounded text-xs ${
                    fc.status === "completed"
                      ? "bg-green-100 text-green-700"
                      : "bg-yellow-100 text-yellow-700"
                  }`}
                >
                  {fc.status}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Format reasoning text - convert markdown bold to proper styling
function formatReasoningText(text: string): React.ReactNode {
  // Simple markdown bold handling
  const parts = text.split(/\*\*(.+?)\*\*/g);
  return parts.map((part, index) => {
    // Odd indices are the bold parts
    if (index % 2 === 1) {
      return (
        <strong key={index} className="font-semibold">
          {part}
        </strong>
      );
    }
    return part;
  });
}

function ThinkingIcon() {
  return (
    <svg
      className="w-4 h-4 text-gray-500"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
      />
    </svg>
  );
}

function ChevronIcon({ isExpanded }: { isExpanded: boolean }) {
  return (
    <svg
      className={`w-4 h-4 text-gray-500 transition-transform ${isExpanded ? "rotate-180" : ""}`}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
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
