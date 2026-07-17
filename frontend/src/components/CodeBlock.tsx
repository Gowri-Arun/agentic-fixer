import { useState, useCallback } from "react";
import { copyToClipboard } from "../utils/clipboard";

interface CodeBlockProps {
  code: string;
  language?: string;
  filePath?: string;
  defaultCollapsed?: boolean;
}

export function CodeBlock({
  code,
  language = "html",
  filePath,
  defaultCollapsed = false,
}: CodeBlockProps) {
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">(
    "idle",
  );
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  const handleCopy = useCallback(async () => {
    setCopyState("copied");
    try {
      await copyToClipboard(code);
      setTimeout(() => setCopyState("idle"), 2000);
    } catch {
      setCopyState("failed");
      setTimeout(() => setCopyState("idle"), 2000);
    }
  }, [code]);

  const toggleCollapse = useCallback(() => {
    setIsCollapsed((prev) => !prev);
  }, []);

  const copyLabel =
    copyState === "copied" ? "Copied" : copyState === "failed" ? "Failed" : "Copy";
  const expandLabel = isCollapsed ? "Show code" : "Hide code";
  const regionId = filePath
    ? `code-region-${filePath.replace(/[^a-z0-9]/gi, "-")}`
    : undefined;

  return (
    <div className="code-block">
      <div className="code-block-header">
        <div className="code-block-meta">
          {filePath && (
            <span className="code-file-path" title={filePath}>
              {filePath}
            </span>
          )}
          <span className="code-language">{language}</span>
        </div>
        <div className="code-block-actions">
          <button
            className="code-toggle-button"
            onClick={toggleCollapse}
            type="button"
            aria-expanded={!isCollapsed}
            aria-controls={regionId}
          >
            {expandLabel}
          </button>
          <button
            className="copy-button"
            onClick={handleCopy}
            type="button"
            aria-label={`Copy ${language} code${filePath ? ` from ${filePath}` : ""}`}
            disabled={copyState !== "idle"}
          >
            {copyLabel}
          </button>
        </div>
      </div>
      <pre
        className={isCollapsed ? "code-block-pre collapsed" : "code-block-pre"}
        id={regionId}
        hidden={isCollapsed}
      >
        <code>{code}</code>
      </pre>
    </div>
  );
}
