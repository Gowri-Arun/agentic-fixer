export function EmptyState() {
  return (
    <div className="card empty-state">
      <h2>Agentic Fixer</h2>
      <p>
        Analyze any web page for agent-readiness issues and get actionable
        fixes tailored to your tech stack.
      </p>
      <ul className="empty-features">
        <li> detects missing structured data</li>
        <li>Identifies trust and policy gaps</li>
        <li>Checks document structure</li>
        <li>Generates stack-specific code fixes</li>
      </ul>
    </div>
  );
}
