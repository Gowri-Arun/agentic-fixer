import type { CategoryScore } from "../utils/categoryScores";

interface ScoreBreakdownProps {
  overallScore: number;
  overallGrade: string;
  categoryScores: CategoryScore[];
}

function getScoreColor(score: number): string {
  if (score >= 80) return "score-high";
  if (score >= 50) return "score-medium";
  return "score-low";
}

export function ScoreBreakdown({
  overallScore,
  overallGrade,
  categoryScores,
}: ScoreBreakdownProps) {
  const overallColorClass = getScoreColor(overallScore);

  return (
    <div className="card score-breakdown">
      <div className="score-bar-group">
        <div className="score-bar-label">
          <span className="score-bar-name">
            Overall: {overallGrade}
          </span>
          <span className="score-bar-value">{overallScore}/100</span>
        </div>
        <div
          className="score-bar-track"
          role="progressbar"
          aria-valuenow={overallScore}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Overall score: ${overallScore} out of 100`}
        >
          <div
            className={`score-bar-fill ${overallColorClass}`}
            style={{ width: `${overallScore}%` }}
          />
        </div>
      </div>

      {categoryScores.map((cat) => {
        const colorClass = getScoreColor(cat.score);
        return (
          <div key={cat.category} className="score-bar-group">
            <div className="score-bar-label">
              <span className="score-bar-name">{cat.label}</span>
              <span className="score-bar-value">{cat.score}/100</span>
            </div>
            <div
              className="score-bar-track"
              role="progressbar"
              aria-valuenow={cat.score}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`${cat.label} score: ${cat.score} out of 100`}
            >
              <div
                className={`score-bar-fill ${colorClass}`}
                style={{ width: `${cat.score}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}