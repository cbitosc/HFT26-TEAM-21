/**
 * Alert component for displaying error, success, and warning messages
 * in auth forms following the SkillProof AI design system.
 */

import React from 'react';
import { AlertCircle, CheckCircle, Info, XCircle } from 'lucide-react';
import { clsx } from 'clsx';

type AlertVariant = 'error' | 'success' | 'warning' | 'info';

interface AlertProps {
  variant: AlertVariant;
  message: string;
  className?: string;
}

const CONFIG: Record<
  AlertVariant,
  { icon: React.ElementType; base: string; text: string }
> = {
  error: {
    icon: XCircle,
    base: 'bg-rose-950/60 border-rose-800/60',
    text: 'text-rose-300',
  },
  success: {
    icon: CheckCircle,
    base: 'bg-emerald-950/60 border-emerald-800/60',
    text: 'text-emerald-300',
  },
  warning: {
    icon: AlertCircle,
    base: 'bg-amber-950/60 border-amber-800/60',
    text: 'text-amber-300',
  },
  info: {
    icon: Info,
    base: 'bg-sky-950/60 border-sky-800/60',
    text: 'text-sky-300',
  },
};

export const Alert: React.FC<AlertProps> = ({ variant, message, className }) => {
  const { icon: Icon, base, text } = CONFIG[variant];
  return (
    <div
      className={clsx(
        'flex items-start gap-3 rounded-xl border px-4 py-3 text-sm',
        base,
        text,
        className
      )}
      role="alert"
    >
      <Icon className="w-4 h-4 mt-0.5 flex-shrink-0" />
      <span>{message}</span>
    </div>
  );
};
