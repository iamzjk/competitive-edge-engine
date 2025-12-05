import { ReactNode, ButtonHTMLAttributes } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: 'primary' | 'secondary' | 'danger'
}

export default function Button({ children, variant = 'primary', className = '', ...props }: ButtonProps) {
  const baseClasses = 'px-4 py-2 rounded-lg font-semibold transition-colors'
  const variantClasses = {
    primary: 'bg-primary text-white hover:bg-primary/90',
    secondary: 'bg-slate-200 text-slate-700 hover:bg-slate-300',
    danger: 'bg-red-500 text-white hover:bg-red-600'
  }

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}

