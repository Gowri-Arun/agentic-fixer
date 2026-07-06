import { useState } from "react";
import { copyToClipboard } from "../utils/clipboard";

interface CodeBlockProps {
  code: string;
  language?: string;
}

export function CodeBlock({ code, language = "html" }: CodeBlockProps) {
  const [buttonText, setButtonText] = useState("Copy");

  const handleCopy = async () => {
    try {
      await copyToClipboard(code);
      setButtonText("Copied");
      setTimeout(() => setButtonText("Copy"), 2000);
    } catch {
      setButtonText("Failed");
      setTimeout(() => setButtonText("Copy"), 2000);
    }
  };

  return (
    <div className="code-block">
      <div className="code-block-header">
        <span className="code-language">{language}</span>
        <button
          className="copy-button"
          onClick={handleCopy}
          type="button"
        >
          {buttonText}
        </button>
      </div>
      <pre>
        <code>{code}</code>
      </pre>
    </div>
  );
}
