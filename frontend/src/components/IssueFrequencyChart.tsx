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

interface IssueFrequencyChartProps {
  results: Array<{ issue_ids: string[] }>;
}

const COLORS = [
  "#2563eb",
  "#22c55e",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
  "#ec4899",
  "#14b8a6",
  "#f97316",
  "#6366f1",
];

export function IssueFrequencyChart({ results }: IssueFrequencyChartProps) {
  const frequencyMap = new Map<string, number>();

  for (const site of results) {
    for (const issueId of site.issue_ids) {
      frequencyMap.set(issueId, (frequencyMap.get(issueId) || 0) + 1);
    }
  }

  const data = Array.from(frequencyMap.entries())
    .map(([detector, count]) => ({
      detector: detector.length > 20 ? detector.slice(0, 18) + "…" : detector,
      fullDetector: detector,
      count,
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  if (data.length === 0) {
    return (
      <div className="chart-empty" role="status">
        No issue data available
      </div>
    );
  }

  return (
    <div className="chart-container">
      <h3>Issue Frequency by Detector</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          aria-label="Issue frequency by detector"
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="detector" tick={{ fontSize: 12 }} />
          <YAxis allowDecimals={false} />
          <Tooltip
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={(value: any) => [Number(value), "Issues"]}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            labelFormatter={(label: any, payload?: any) =>
              payload?.[0]?.payload?.fullDetector || label
            }
          />
          <Bar dataKey="count" name="Issues" radius={[4, 4, 0, 0]}>
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <table className="chart-table" aria-label="Issue frequency data">
        <thead>
          <tr>
            <th>Detector</th>
            <th>Count</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={item.fullDetector}>
              <td>{item.fullDetector}</td>
              <td>{item.count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
