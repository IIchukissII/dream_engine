export default function ExpandableCard({
  id,
  icon,
  title,
  summary,
  children,
  isExpanded,
  onToggle
}) {
  return (
    <div
      className={`expandable-card ${isExpanded ? 'expandable-card--expanded' : ''}`}
      onClick={() => onToggle(id)}
    >
      <div className="expandable-card__header">
        <div>
          {icon && <div className="expandable-card__icon">{icon}</div>}
          <h3 className="expandable-card__title">{title}</h3>
          <p className="expandable-card__summary">{summary}</p>
        </div>
        <span className="expandable-card__chevron">&#9660;</span>
      </div>

      <div className="expandable-card__details">
        <div className="expandable-card__details-content">
          {children}
        </div>
      </div>
    </div>
  )
}
