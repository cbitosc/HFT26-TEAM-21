/**
 * Reusable Button component following the SkillProof AI design system.
 */

import React from 'react';
import { clsx } from 'clsx';
import { Loader2 } from 'lucide-react';

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  isLoading?: boolean;
  fullWidth?: boolean;
  children: React.ReactNode;
}

const VARIANTS: Record<ButtonVariant, string> = {
  primary:
    'bg-sky-600 hover:bg-sky-500 active:bg-sky-700 text-white border-transparent shadow-lg shadow-sky-600/20',
  secondary:
    'bg-slate-800 hover:bg-slate-700 active:bg-slate-900 text-slate-200 border-slate-700',
  danger:
    'bg-rose-700 hover:bg-rose-600 active:bg-rose-800 text-white border-transparent',
  ghost:
    'bg-transparent hover:bg-slate-800 text-slate-400 hover:text-slate-200 border-slate-800',
};

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  isLoading = false,
  fullWidth = false,
  disabled,
  className,
  children,
  ...props
}) => (
  <button
    disabled={disabled || isLoading}
    className={clsx(
      'inline-flex items-center justify-center gap-2 rounded-xl border px-5 py-2.5',
      'text-sm font-medium transition-all duration-150',
      'focus:outline-none focus:ring-2 focus:ring-sky-500/50',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      VARIANTS[variant],
      fullWidth && 'w-full',
      className
    )}
    {...props}
  >
    {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
    {children}
  </button>
);
