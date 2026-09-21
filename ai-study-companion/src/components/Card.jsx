export default function Card({ children, className = '', as: Tag = 'div', ...props }) {
  return (
    <Tag className={`card ${className}`} {...props}>
      {children}
    </Tag>
  )
}

export function CardHeader({ title, subtitle, action }) {
  return (
    <div className="mb-4 flex items-start justify-between gap-4">
      <div>
        <h3 className="section-title">{title}</h3>
        {subtitle && <p className="muted mt-0.5">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}
