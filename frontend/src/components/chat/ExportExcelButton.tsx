"use client";

import { useState } from "react";
import { useAuthStore } from "@/lib/store";
import { ReportPath } from "@/lib/websocket-message-handler";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

interface ExportExcelButtonProps {
  reportPath: ReportPath;  // File path (e.g., "sessions/ws_id/outputs/report.xlsx")
}

export function ExportExcelButton({ reportPath }: ExportExcelButtonProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { tokens } = useAuthStore();

  const handleExport = async () => {
    setIsExporting(true);
    setError(null);

    try {
      // Download the pre-generated Excel file from the backend
      // reportPath format: "sessions/ws_id/outputs/report.xlsx"
      const downloadUrl = `${API_BASE_URL}/api/chat/download/${reportPath}`;

      const response = await fetch(downloadUrl, {
        method: "GET",
        headers: {
          // Add auth header if needed in future
          // "Authorization": `Bearer ${tokens?.accessToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || "Failed to download Excel file");
      }

      // Extract filename from reportPath (e.g., "report.xlsx" from "sessions/ws_id/outputs/report.xlsx")
      const filename = reportPath.split('/').pop() || 'report.xlsx';

      // Get the blob and download it
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download error:", err);
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="mt-3">
      <button
        onClick={handleExport}
        disabled={isExporting}
        className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white text-sm font-medium rounded-lg transition-colors"
      >
        <DownloadIcon className="w-4 h-4" />
        {isExporting ? (
          "Downloading..."
        ) : (
          "Download Excel Report"
        )}
      </button>
      
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
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
