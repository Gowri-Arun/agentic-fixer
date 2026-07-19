import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface PageTypeScoresChartProps {
  scoresByPageType: Record<string, number>;
}

function getScoreColor(score: number): string {
  if (score >= 80) return "#22c55e";
  if (score >= 50) return "#f59e0b";
  return "#ef4444";
}

export function PageTypeScoresChart({ scoresByPageType }: PageTypeScoresChartProps) {
  const data = Object.entries(scoresByPageType)
    .map(([pageType, score]) => ({
      pageType,
      score: Math.round(score),
    }))
    .sort((a, b) => b.score - a.score);

  if (data.length === 0) {
    return (
      <div className="chart-empty" role="status">
        No page type data available
      </div>
    );
  }

  return (
    <div className="chart-container">
      <h3>Average Score by Page Type</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          aria-label="Average score by page type"
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="pageType" tick={{ fontSize: 12 }} />
          <YAxis domain={[0, 100]} />
          <Tooltip
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={(value: any) => [Number(value), "Score"]}
          />
          <Bar dataKey="score" name="Score" radius={[4, 4, 0, 0]}>
            {data.map((entry) => (
              <Cell key={entry.pageType} fill={getScoreColor(entry.score)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <table className="chart-table" aria-label="Page type score data">
        <thead>
          <tr>
            <th>Page Type</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={item.pageType}>
              <td>{item.pageType}</td>
              <td>{item.score}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
