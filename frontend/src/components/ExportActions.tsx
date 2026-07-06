import { useState } from "react";
import { copyToClipboard } from "../utils/clipboard";
import {
  buildFixesExportContent,
  buildJsonExportContent,
  downloadTextFile,
} from "../utils/export";
import type { AnalyzeResponse } from "../types/audit";

interface ExportActionsProps {
  result: AnalyzeResponse;
}

export function ExportActions({ result }: ExportActionsProps) {
  const [copyJsonText, setCopyJsonText] = useState("Copy JSON");
  const [copyMarkdownText, setCopyMarkdownText] = useState("Copy Markdown");
  const [copyFixesText, setCopyFixesText] = useState("Copy All Fixes");

  const handleCopyJson = async () => {
    try {
      const content = buildJsonExportContent(result);
      await copyToClipboard(content);
      setCopyJsonText("Copied");
      setTimeout(() => setCopyJsonText("Copy JSON"), 2000);
    } catch {
      setCopyJsonText("Failed");
      setTimeout(() => setCopyJsonText("Copy JSON"), 2000);
    }
  };

  const handleDownloadJson = () => {
    const content = buildJsonExportContent(result);
    downloadTextFile("agentic-fixer-report.json", content, "application/json");
  };

  const handleCopyMarkdown = async () => {
    try {
      await copyToClipboard(result.markdown_report);
      setCopyMarkdownText("Copied");
      setTimeout(() => setCopyMarkdownText("Copy Markdown"), 2000);
    } catch {
      setCopyMarkdownText("Failed");
      setTimeout(() => setCopyMarkdownText("Copy Markdown"), 2000);
    }
  };

  const handleDownloadMarkdown = () => {
    downloadTextFile(
      "agentic-fixer-report.md",
      result.markdown_report,
      "text/markdown",
    );
  };

  const handleCopyFixes = async () => {
    try {
      const content = buildFixesExportContent(result.fixes);
      await copyToClipboard(content);
      setCopyFixesText("Copied");
      setTimeout(() => setCopyFixesText("Copy All Fixes"), 2000);
    } catch {
      setCopyFixesText("Failed");
      setTimeout(() => setCopyFixesText("Copy All Fixes"), 2000);
    }
  };

  return (
    <div className="card export-actions">
      <h3>Export Results</h3>
      <div className="export-buttons">
        <button className="export-button" onClick={handleCopyJson} type="button">
          {copyJsonText}
        </button>
        <button
          className="export-button"
          onClick={handleDownloadJson}
          type="button"
        >
          Download JSON
        </button>
        <button
          className="export-button"
          onClick={handleCopyMarkdown}
          type="button"
        >
          {copyMarkdownText}
        </button>
        <button
          className="export-button"
          onClick={handleDownloadMarkdown}
          type="button"
        >
          Download Markdown
        </button>
        <button
          className="export-button"
          onClick={handleCopyFixes}
          type="button"
        >
          {copyFixesText}
        </button>
      </div>
    </div>
  );
}
