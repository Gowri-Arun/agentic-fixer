import { useState } from "react";
import type { TargetStack } from "../types/audit";

interface AnalyzeFormProps {
  onSubmit: (url: string, targetStack: TargetStack) => void;
  isLoading: boolean;
}

const STACK_OPTIONS: { value: TargetStack; label: string }[] = [
  { value: "nextjs-13", label: "Next.js 13 App Router" },
  { value: "react-spa", label: "React SPA" },
  { value: "plain-html", label: "Plain HTML" },
];

export function AnalyzeForm({ onSubmit, isLoading }: AnalyzeFormProps) {
  const [url, setUrl] = useState("");
  const [targetStack, setTargetStack] = useState<TargetStack>("nextjs-13");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      onSubmit(url.trim(), targetStack);
    }
  };

  return (
    <form className="analyze-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="url">Page URL</label>
        <input
          id="url"
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          required
          disabled={isLoading}
        />
      </div>
      <div className="form-group">
        <label htmlFor="target-stack">Target Stack</label>
        <select
          id="target-stack"
          value={targetStack}
          onChange={(e) => setTargetStack(e.target.value as TargetStack)}
          disabled={isLoading}
        >
          {STACK_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      <button type="submit" disabled={isLoading || !url.trim()}>
        {isLoading ? "Analyzing..." : "Analyze"}
      </button>
    </form>
  );
}
