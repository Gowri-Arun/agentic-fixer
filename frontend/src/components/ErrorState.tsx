interface ErrorStateProps {
  message: string;
}

export function ErrorState({ message }: ErrorStateProps) {
  return (
    <div className="card error-card">
      <div className="error-icon">!</div>
      <p className="error-message">{message}</p>
    </div>
  );
}
