export default function Card({ title, eyebrow, action, children, className = "" }) {
  return (
    <div className={`bg-base-700 border border-base-500 rounded-lg shadow-panel ${className}`}>
      {(title || eyebrow || action) && (
        <div className="flex items-center justify-between px-5 pt-4 pb-3 border-b border-base-500">
          <div>
            {eyebrow && (
              <div className="text-xs font-mono uppercase tracking-wider text-ink-500 mb-1">
                {eyebrow}
              </div>
            )}
            {title && <h3 className="text-sm font-semibold text-ink-100">{title}</h3>}
          </div>
          {action}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}
