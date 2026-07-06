export type TargetStack = "nextjs-13" | "react-spa" | "plain-html";
export type Severity = "low" | "medium" | "high";
export type FixPriority = "low" | "medium" | "high";

export interface AnalyzeRequest {
  url: string;
  target_stack: TargetStack;
}

export interface Issue {
  id: string;
  severity: Severity;
  category: string;
  location: string;
  description: string;
}

export interface Fix {
  issue_id: string;
  title: string;
  priority: FixPriority;
  why_it_matters: string;
  code_snippet: string;
  instructions: string[];
}

export interface AuditMetadata {
  url: string;
  location: string;
  target_stack: TargetStack;
  checked_at: string;
  issue_count: number;
  fix_count: number;
  detectors_run: string[];
}

export interface AnalyzeResponse {
  score: number;
  grade: string;
  summary: string;
  issues: Issue[];
  fixes: Fix[];
  metadata: AuditMetadata;
  markdown_report: string;
}
