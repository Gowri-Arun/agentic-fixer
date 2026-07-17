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
  file_path?: string;
  language?: string;
}

export interface EvidenceField {
  name: string;
  value: string | number | boolean | string[];
  unit?: string;
}

export interface DetectorEvidence {
  fields: EvidenceField[];
}

export interface DetectorResult {
  detector_id: string;
  display_name: string;
  decision: "detected" | "not_detected" | "skipped" | "error";
  issues: Record<string, unknown>[];
  evidence: DetectorEvidence;
  confidence: number;
  duration_ms: number;
  version: string;
  skipped_reason?: string;
}

export interface AuditMetadata {
  url: string;
  location: string;
  target_stack: TargetStack;
  checked_at: string;
  issue_count: number;
  fix_count: number;
  detectors_run: string[];
  detector_results?: DetectorResult[];
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

export interface ExamplePage {
  id: string;
  title: string;
  description: string;
  expected_issues: string[];
}

export interface DemoAnalyzeRequest {
  example_id: string;
  target_stack: TargetStack;
}
