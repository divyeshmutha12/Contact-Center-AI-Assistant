"use client";

import { useEffect, useRef, useState } from "react";
import {
  Chart,
  registerables,
  ChartType,
  ChartData,
  ChartOptions,
} from "chart.js";
import { ChartConfig } from "@/lib/websocket-message-handler";

// Register all Chart.js components
Chart.register(...registerables);

interface ChartRendererProps {
  chartConfig: ChartConfig;
  className?: string;
}

export function ChartRenderer({ chartConfig, className = "" }: ChartRendererProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);

  // Get chart title from options or generate from type
  const getChartTitle = (): string => {
    if (chartConfig.options?.plugins?.title?.text) {
      return chartConfig.options.plugins.title.text;
    }
    // Capitalize chart type as fallback
    return `${chartConfig.type.charAt(0).toUpperCase() + chartConfig.type.slice(1)} Chart`;
  };

  // Download chart as PNG
  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering expand/collapse

    if (!canvasRef.current) return;

    // Get the canvas data as PNG
    const dataUrl = canvasRef.current.toDataURL("image/png", 1.0);

    // Create temporary link and trigger download
    const link = document.createElement("a");
    link.download = `${getChartTitle().replace(/[^a-zA-Z0-9]/g, "_")}.png`;
    link.href = dataUrl;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  useEffect(() => {
    // Only render chart when expanded
    if (!isExpanded || !canvasRef.current) return;

    // Destroy existing chart if any
    if (chartRef.current) {
      chartRef.current.destroy();
    }

    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return;

    // Create new chart with the config from backend
    // Using type assertion since backend sends complete Chart.js config
    chartRef.current = new Chart(ctx, {
      type: chartConfig.type as ChartType,
      data: chartConfig.data as ChartData,
      options: {
        ...(chartConfig.options as ChartOptions),
        responsive: true,
        maintainAspectRatio: true,
      },
    });

    // Cleanup on unmount or collapse
    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [chartConfig, isExpanded]);

  return (
    <div className={`w-full ${className}`}>
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {/* Collapsible Header */}
        <div
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors text-left cursor-pointer"
        >
          <div className="flex items-center gap-3">
            <ChartIcon />
            <div>
              <p className="text-sm font-medium text-gray-900">{getChartTitle()}</p>
              <p className="text-xs text-gray-500">Interactive chart</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Download button - only show when expanded */}
            {isExpanded && (
              <button
                onClick={handleDownload}
                className="p-1.5 rounded-md hover:bg-gray-200 transition-colors"
                title="Download as PNG"
              >
                <DownloadIcon className="w-4 h-4 text-gray-500" />
              </button>
            )}
            <ExpandIcon isExpanded={isExpanded} />
          </div>
        </div>

        {/* Expanded Chart Content */}
        {isExpanded && (
          <div className="border-t border-gray-200 p-4">
            <div className="max-h-[400px] flex items-center justify-center">
              <canvas ref={canvasRef} style={{ maxHeight: '380px' }} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ChartIcon() {
  return (
    <svg
      className="w-5 h-5 text-gray-500"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
      />
    </svg>
  );
}

function ExpandIcon({ isExpanded }: { isExpanded: boolean }) {
  if (isExpanded) {
    // Collapse icon (X)
    return (
      <svg
        className="w-5 h-5 text-gray-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M6 18L18 6M6 6l12 12"
        />
      </svg>
    );
  }
  // Expand icon (arrows pointing outward)
  return (
    <svg
      className="w-5 h-5 text-gray-400"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
      />
    </svg>
  );
}

function DownloadIcon({ className }: { className?: string }) {
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
        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
      />
    </svg>
  );
}
