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

interface ValidationWarningsChartProps {
  results: Array<{ error_category: string }>;
}

const ERROR_COLORS: Record<string, string> = {
  timeout: "#f59e0b",
  dns_failure: "#ef4444",
  connection_failure: "#ef4444",
  http_rejection: "#f97316",
  parsing_failure: "#8b5cf6",
  internal_failure: "#ef4444",
  unknown: "#6b7280",
};

export function ValidationWarningsChart({ results }: ValidationWarningsChartProps) {
  const categoryMap = new Map<string, number>();

  for (const site of results) {
    if (site.error_category) {
      categoryMap.set(site.error_category, (categoryMap.get(site.error_category) || 0) + 1);
    }
  }

  const data = Array.from(categoryMap.entries())
    .map(([category, count]) => ({
      category,
      count,
    }))
    .sort((a, b) => b.count - a.count);

  if (data.length === 0) {
    return (
      <div className="chart-empty" role="status">
        No validation warnings available
      </div>
    );
  }

  return (
    <div className="chart-container">
      <h3>Validation Warnings by Category</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          aria-label="Validation warnings by category"
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="category" tick={{ fontSize: 12 }} />
          <YAxis allowDecimals={false} />
          <Tooltip
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={(value: any) => [Number(value), "Warnings"]}
          />
          <Bar dataKey="count" name="Warnings" radius={[4, 4, 0, 0]}>
            {data.map((entry) => (
              <Cell
                key={entry.category}
                fill={ERROR_COLORS[entry.category] || "#6b7280"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <table className="chart-table" aria-label="Validation warning data">
        <thead>
          <tr>
            <th>Category</th>
            <th>Count</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={item.category}>
              <td>{item.category}</td>
              <td>{item.count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
