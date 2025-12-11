/**
 * Chart.js Data Interfaces
 *
 * This file contains all the interfaces related to Chart.js
 * configuration and data structures.
 */

// ============================================
// Chart.js Dataset Interface
// ============================================

export interface ChartDataset {
  label: string;
  data: number[];
  backgroundColor?: string[];
  borderColor?: string[];
  borderWidth?: number;
}

// ============================================
// Chart.js Data Interface
// ============================================

export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

// ============================================
// Chart.js Options Interface
// ============================================

export interface ChartOptions {
  responsive?: boolean;
  plugins?: {
    legend?: { display?: boolean; position?: string };
    title?: { display?: boolean; text?: string };
  };
  scales?: {
    y?: { beginAtZero?: boolean };
    x?: { beginAtZero?: boolean };
  };
}

// ============================================
// Chart.js Configuration Interface
// ============================================

export interface ChartConfig {
  type: string; // "bar", "line", "pie", "doughnut", etc.
  data: ChartData;
  options?: ChartOptions;
}
