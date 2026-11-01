/**
 * Reusable form input component following the SkillProof AI design system.
 * Supports left icons, show/hide password toggling, error validation states, and accessibility.
 */

import React, { forwardRef, useState } from 'react';
import { clsx } from 'clsx';
import { Eye, EyeOff } from 'lucide-react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
  leftIcon?: React.ReactNode;
  rightElement?: React.ReactNode;
  isPassword?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      hint,
      className,
      id,
      type = 'text',
      leftIcon,
      rightElement,
      isPassword,
      disabled,
      ...props
    },
    ref
  ) => {
    const inputId = id || label.toLowerCase().replace(/\s+/g, '-');
    const [showPassword, setShowPassword] = useState(false);

    const effectiveType = isPassword ? (showPassword ? 'text' : 'password') : type;

    return (
      <div className="space-y-1.5 w-full">
        <label htmlFor={inputId} className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
          {label}
        </label>
        <div className="relative flex items-center">
          {leftIcon && (
            <div className="absolute left-3.5 flex items-center pointer-events-none text-slate-400">
              {leftIcon}
            </div>
          )}
          <input
            id={inputId}
            ref={ref}
            type={effectiveType}
            disabled={disabled}
            className={clsx(
              'w-full py-2.5 rounded-xl bg-slate-900/90 border text-slate-100 text-sm shadow-inner',
              'placeholder-slate-500 outline-none transition-all duration-200',
              'focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500',
              disabled && 'opacity-60 cursor-not-allowed bg-slate-900/40',
              leftIcon ? 'pl-10' : 'pl-4',
              isPassword || rightElement ? 'pr-11' : 'pr-4',
              error
                ? 'border-rose-500/80 focus:ring-rose-500/50 focus:border-rose-500'
                : 'border-slate-800 hover:border-slate-700',
              className
            )}
            aria-invalid={Boolean(error)}
            {...props}
          />
          {isPassword && (
            <button
              type="button"
              tabIndex={-1}
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3.5 p-1 rounded-md text-slate-400 hover:text-slate-200 focus:outline-none transition-colors"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          )}
          {rightElement && !isPassword && (
            <div className="absolute right-3.5 flex items-center">
              {rightElement}
            </div>
          )}
        </div>
        {error && (
          <p className="text-xs text-rose-400 font-medium flex items-center gap-1.5 mt-1">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400 inline-block" />
            {error}
          </p>
        )}
        {hint && !error && (
          <p className="text-xs text-slate-400 mt-1">{hint}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
