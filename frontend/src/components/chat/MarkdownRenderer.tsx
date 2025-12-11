"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useMemo } from "react";
import { ExportExcelButton } from "./ExportExcelButton";

// Type for export data extracted from content
export interface ExportData {
  filename: string;
  total_records: number;
  data: Record<string, unknown>[];
}

interface MarkdownRendererProps {
  content: string;
  className?: string;
  onExportDataFound?: (data: ExportData | null) => void;
}

// Extract export data from content and return clean content
function extractExportData(content: string): { cleanContent: string; exportData: ExportData | null } {
  const exportRegex = /\[EXPORT_DATA\]\s*([\s\S]*?)\s*\[\/EXPORT_DATA\]/;
  const match = content.match(exportRegex);

  if (!match) {
    return { cleanContent: content, exportData: null };
  }

  try {
    const jsonStr = match[1].trim();
    const exportData = JSON.parse(jsonStr) as ExportData;

    // Validate the structure
    if (!exportData.filename || !exportData.data || !Array.isArray(exportData.data)) {
      console.warn("Invalid export data structure:", exportData);
      return { cleanContent: content, exportData: null };
    }

    // Remove the export block from content
    const cleanContent = content.replace(exportRegex, "").trim();

    return { cleanContent, exportData };
  } catch (err) {
    console.error("Failed to parse export data:", err);
    return { cleanContent: content, exportData: null };
  }
}

export function MarkdownRenderer({ content, className = "" }: MarkdownRendererProps) {
  // Extract export data and clean content
  const { cleanContent, exportData } = useMemo(() => extractExportData(content), [content]);

  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Headings
          h1: ({ children }) => (
            <h1 className="text-xl font-bold mb-3 mt-4 first:mt-0">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-bold mb-2 mt-3 first:mt-0">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-semibold mb-2 mt-3 first:mt-0">{children}</h3>
          ),
          h4: ({ children }) => (
            <h4 className="text-sm font-semibold mb-1 mt-2 first:mt-0">{children}</h4>
          ),

          // Paragraphs
          p: ({ children }) => (
            <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
          ),

          // Lists
          ul: ({ children }) => (
            <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="text-sm">{children}</li>
          ),

          // Code
          code: ({ className, children, ...props }) => {
            const isInline = !className;
            if (isInline) {
              return (
                <code className="bg-gray-200 px-1 py-0.5 rounded text-sm font-mono" {...props}>
                  {children}
                </code>
              );
            }
            return (
              <code className={`${className} block bg-gray-800 text-gray-100 p-3 rounded-lg text-sm font-mono overflow-x-auto`} {...props}>
                {children}
              </code>
            );
          },
          pre: ({ children }) => (
            <pre className="mb-2 overflow-x-auto">{children}</pre>
          ),

          // Links
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 underline"
            >
              {children}
            </a>
          ),

          // Blockquotes
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-gray-300 pl-3 italic text-gray-600 mb-2">
              {children}
            </blockquote>
          ),

          // Tables (GFM)
          table: ({ children }) => (
            <div className="overflow-x-auto mb-2">
              <table className="min-w-full border border-gray-300 text-sm">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-gray-100">{children}</thead>
          ),
          tbody: ({ children }) => (
            <tbody>{children}</tbody>
          ),
          tr: ({ children }) => (
            <tr className="border-b border-gray-200">{children}</tr>
          ),
          th: ({ children }) => (
            <th className="px-3 py-2 text-left font-semibold">{children}</th>
          ),
          td: ({ children }) => (
            <td className="px-3 py-2">{children}</td>
          ),

          // Horizontal rule
          hr: () => <hr className="my-4 border-gray-300" />,

          // Strong and emphasis
          strong: ({ children }) => (
            <strong className="font-semibold">{children}</strong>
          ),
          em: ({ children }) => (
            <em className="italic">{children}</em>
          ),
        }}
      >
        {cleanContent}
      </ReactMarkdown>

      {/* Show Export Excel button if export data was found */}
      {exportData && <ExportExcelButton exportData={exportData} />}
    </div>
  );
}
