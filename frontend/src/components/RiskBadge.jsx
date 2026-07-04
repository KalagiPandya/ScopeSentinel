const RISK_COLORS = {
  low: "#4ADE80",
  medium: "#FBBF24",
  high: "#FB923C",
  critical: "#F87171",
};

const RISK_LABELS = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};

/**
 * Signature element: a pulsing dot + label used everywhere risk/status
 * is shown — Dashboard cards, Change Center rows, PR Review results.
 * The pulse ring gives the dashboard a "live system" feel.
 */
export default function RiskBadge({ level, score, showScore = true, size = "md" }) {
  const color = RISK_COLORS[level] || RISK_COLORS.low;
  const label = RISK_LABELS[level] || level;

  const textSize = size === "sm" ? "text-xs" : "text-sm";

  return (
    <span className={`inline-flex items-center gap-2 font-mono ${textSize} text-ink-100`}>
      <span className="pulse-dot" style={{ backgroundColor: color }} aria-hidden="true" />
      <span style={{ color }} className="font-semibold">{label}</span>
      {showScore && score !== undefined && score !== null && (
        <span className="text-ink-500">{score}/100</span>
      )}
    </span>
  );
}

export { RISK_COLORS, RISK_LABELS };
