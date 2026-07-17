import type { Fix } from "../types/audit";
import { CodeBlock } from "./CodeBlock";

interface FixCardProps {
  fix: Fix;
}

const PRIORITY_CLASSES: Record<string, string> = {
  high: "priority-high",
  medium: "priority-medium",
  low: "priority-low",
};

export function FixCard({ fix }: FixCardProps) {
  const priorityClass = PRIORITY_CLASSES[fix.priority] ?? "";

  return (
    <div className="card fix-card">
      <div className="fix-header">
        <h3 className="fix-title">{fix.title}</h3>
        <span className={`badge ${priorityClass}`}>{fix.priority}</span>
      </div>
      <p className="fix-issue-id">
        <strong>Related issue:</strong> {fix.issue_id}
      </p>
      <p className="fix-why">{fix.why_it_matters}</p>

      {fix.instructions.length > 0 && (
        <div className="fix-instructions">
          <strong>Instructions:</strong>
          <ol>
            {fix.instructions.map((instruction, index) => (
              <li key={index}>{instruction}</li>
            ))}
          </ol>
        </div>
      )}

      {fix.code_snippet && (
        <div className="fix-code">
          <strong>Code snippet:</strong>
          <CodeBlock
            code={fix.code_snippet}
            language={fix.language ?? "html"}
            filePath={fix.file_path}
          />
        </div>
      )}
    </div>
  );
}
