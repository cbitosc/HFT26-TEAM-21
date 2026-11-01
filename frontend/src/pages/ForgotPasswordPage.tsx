/**
 * ForgotPasswordPage — sends a password reset email via Supabase Auth.
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft, Send } from 'lucide-react';
import { AuthLayout } from '../components/AuthLayout';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { Alert } from '../components/Alert';
import { useAuth } from '../contexts/AuthContext';

export const ForgotPasswordPage: React.FC = () => {
  const { resetPassword, isConfigured } = useAuth();
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading) return;
    setError(null);

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail) {
      setError('Please provide your registered email address.');
      return;
    }

    setIsLoading(true);
    const err = await resetPassword(cleanEmail);
    setIsLoading(false);

    if (err) {
      setError(err);
    } else {
      setSuccess(true);
    }
  };

  if (success) {
    return (
      <AuthLayout
        title="Check your email"
        subtitle="We sent a secure password recovery link to your inbox."
      >
        <div className="space-y-6 text-center">
          <Alert
            variant="success"
            message={`A password reset link was dispatched to ${email}. Please check your inbox and follow the instructions.`}
          />
          <Link
            to="/login"
            className="inline-flex items-center justify-center gap-2 text-sm text-indigo-400 hover:text-indigo-300 font-semibold transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to Sign In</span>
          </Link>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Reset your password"
      subtitle="Enter your account email address and we will send you a recovery link."
    >
      <form onSubmit={handleSubmit} noValidate className="space-y-5">
        {error && <Alert variant="error" message={error} />}

        <Input
          label="Account email address"
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="name@university.edu"
          autoComplete="email"
          required
          disabled={isLoading}
          leftIcon={<Mail className="w-4 h-4" />}
        />

        <Button
          type="submit"
          fullWidth
          isLoading={isLoading}
          disabled={!isConfigured || isLoading}
          className="bg-gradient-to-r from-indigo-600 to-sky-500 hover:from-indigo-500 hover:to-sky-400 text-white font-semibold py-3 rounded-xl shadow-lg shadow-indigo-600/25 transition-all"
        >
          <span className="flex items-center justify-center gap-2">
            <span>Send Reset Link</span>
            {!isLoading && <Send className="w-4 h-4" />}
          </span>
        </Button>
      </form>

      <div className="mt-8 pt-6 border-t border-slate-800/80 text-center text-sm text-slate-400">
        <Link
          to="/login"
          className="text-indigo-400 hover:text-indigo-300 font-semibold inline-flex items-center gap-1.5 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Sign In</span>
        </Link>
      </div>
    </AuthLayout>
  );
};
