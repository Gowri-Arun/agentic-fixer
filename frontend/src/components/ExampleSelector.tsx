import { useEffect, useState } from "react";
import { analyzeDemoPage, getExamples } from "../api/analyze";
import type { AnalyzeResponse, ExamplePage, TargetStack } from "../types/audit";

interface ExampleSelectorProps {
  targetStack: TargetStack;
  onResult: (result: AnalyzeResponse) => void;
  onError: (error: string) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}

export function ExampleSelector({
  targetStack,
  onResult,
  onError,
  isLoading,
  setIsLoading,
}: ExampleSelectorProps) {
  const [examples, setExamples] = useState<ExamplePage[]>([]);

  useEffect(() => {
    const fetchExamples = async () => {
      try {
        const data = await getExamples();
        setExamples(data);
      } catch (err) {
        console.error("Failed to fetch examples:", err);
      }
    };

    fetchExamples();
  }, []);

  const handleExampleClick = async (exampleId: string) => {
    setError(null);
    setIsLoading(true);

    try {
      const response = await analyzeDemoPage({
        example_id: exampleId,
        target_stack: targetStack,
      });
      onResult(response);
    } catch (err) {
      onError(
        err instanceof Error ? err.message : "An unexpected error occurred",
      );
    } finally {
      setIsLoading(false);
    }
  };

  const setError = (error: string | null) => {
    onError(error ?? "");
  };

  if (examples.length === 0) {
    return null;
  }

  return (
    <div className="card examples-section">
      <h2>Or try a deterministic demo:</h2>
      <div className="examples-grid">
        {examples.map((example) => (
          <button
            key={example.id}
            className="example-button"
            onClick={() => handleExampleClick(example.id)}
            disabled={isLoading}
            type="button"
          >
            <span className="example-title">{example.title}</span>
            <span className="example-description">{example.description}</span>
            {example.expected_issues.length > 0 && (
              <span className="example-issues">
                Expected: {example.expected_issues.join(", ")}
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
