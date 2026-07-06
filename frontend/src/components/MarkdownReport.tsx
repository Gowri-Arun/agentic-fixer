import { useState } from "react";
import { copyToClipboard } from "../utils/clipboard";

interface MarkdownReportProps {
  markdown: string;
}

export function MarkdownReport({ markdown }: MarkdownReportProps) {
  const [buttonText, setButtonText] = useState("Copy Report");

  const handleCopy = async () => {
    try {
      await copyToClipboard(markdown);
      setButtonText("Copied!");
      setTimeout(() => setButtonText("Copy Report"), 2000);
    } catch {
      setButtonText("Failed");
      setTimeout(() => setButtonText("Copy Report"), 2000);
    }
  };

  return (
    <details className="card markdown-report">
      <summary className="markdown-header">
        <span>Markdown Report</span>
        <button
          className="copy-button"
          onClick={(e) => {
            e.stopPropagation();
            handleCopy();
          }}
          type="button"
        >
          {buttonText}
        </button>
      </summary>
      <pre className="markdown-content">
        <code>{markdown}</code>
      </pre>
    </details>
  );
}
