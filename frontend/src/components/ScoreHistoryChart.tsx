import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface ScoreHistoryChartProps {
  runs: Array<{
    started_at: string;
    summary: { average_score: number };
  }>;
}

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export function ScoreHistoryChart({ runs }: ScoreHistoryChartProps) {
  const sortedRuns = [...runs].sort(
    (a, b) => new Date(a.started_at).getTime() - new Date(b.started_at).getTime()
  );

  const data = sortedRuns.map((run, index) => ({
    run: `Run ${index + 1}`,
    date: formatTimestamp(run.started_at),
    score: Math.round(run.summary.average_score),
  }));

  if (data.length === 0) {
    return (
      <div className="chart-empty" role="status">
        No score history available
      </div>
    );
  }

  return (
    <div className="chart-container">
      <h3>Score History</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          aria-label="Score history over runs"
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="run" tick={{ fontSize: 12 }} />
          <YAxis domain={[0, 100]} />
          <Tooltip
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={(value: any) => [Number(value), "Score"]}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            labelFormatter={(label: any, payload?: any) =>
              `${label} (${payload?.[0]?.payload?.date || ""})`
            }
          />
          <Line
            type="monotone"
            dataKey="score"
            name="Score"
            stroke="#2563eb"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
      <table className="chart-table" aria-label="Score history data">
        <thead>
          <tr>
            <th>Run</th>
            <th>Date</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={item.run}>
              <td>{item.run}</td>
              <td>{item.date}</td>
              <td>{item.score}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
