export default function Card({
  children,
  className = '',
  hoverEffect = false,
  as: Tag = 'div',
  ...props
}) {
  return (
    <Tag
      className={`card ${hoverEffect ? 'card-hover' : ''} ${className}`}
      {...props}
    >
      {children}
    </Tag>
  )
}

export function CardHeader({ title, subtitle, action, badge }) {
  return (
    <div className="mb-4 flex items-start justify-between gap-4">
      <div>
        <div className="flex items-center gap-2">
          <h3 className="section-title">{title}</h3>
          {badge}
        </div>
        {subtitle && <p className="muted mt-0.5 text-xs">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}
