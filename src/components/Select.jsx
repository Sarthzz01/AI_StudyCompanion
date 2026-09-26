import { useId } from 'react'

export default function Select({ label, options = [], className = '', ...props }) {
  const id = useId()
  return (
    <div className={className}>
      {label && (
        <label htmlFor={id} className="label">
          {label}
        </label>
      )}
      <select id={id} className="field" {...props}>
        {options.map((option) => {
          const value = typeof option === 'string' ? option : option.value
          const text = typeof option === 'string' ? option : option.label
          return (
            <option key={value} value={value}>
              {text}
            </option>
          )
        })}
      </select>
    </div>
  )
}
