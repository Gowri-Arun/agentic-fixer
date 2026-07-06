import { useState } from "react";
import { analyzePage } from "./api/analyze";
import { AnalyzeForm } from "./components/AnalyzeForm";
import type { AnalyzeResponse, TargetStack } from "./types/audit";

function App() {
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (url: string, targetStack: TargetStack) => {
    setError(null);
    setIsLoading(true);

    try {
      const response = await analyzePage({ url, target_stack: targetStack });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Agentic Fixer</h1>
        <p>Analyze web pages for agent-readiness issues</p>
      </header>
      <main className="main">
        <div className="card">
          <AnalyzeForm onSubmit={handleAnalyze} isLoading={isLoading} />
        </div>

        {error && (
          <div className="card error-card">
            <p className="error-message">{error}</p>
          </div>
        )}

        {result && (
          <div className="results-placeholder">
            <p>Results will appear here...</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
