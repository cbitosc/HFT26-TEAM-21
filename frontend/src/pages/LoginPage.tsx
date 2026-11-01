/**
 * LoginPage — Premium SaaS sign-in page.
 *
 * Requirements:
 * - Email address input with Mail icon.
 * - Password input with show/hide toggle and Lock icon.
 * - Remember me checkbox with persistent email storage.
 * - Forgot password link to /forgot-password.
 * - Sign In button with loading spinner and duplicate submission prevention.
 * - Link to Create Account (/register).
 * - Human-readable error messages for wrong credentials, unverified emails, and offline states.
 * - Preserves existing Supabase auth and role-based redirect.
 */

import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Mail, Lock, LogIn, ArrowRight, Sparkles, Compass } from 'lucide-react';
import { AuthLayout } from '../components/AuthLayout';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { Alert } from '../components/Alert';
import { useAuth } from '../contexts/AuthContext';

const REMEMBER_EMAIL_KEY = 'skillproof_remembered_email';

export const LoginPage: React.FC = () => {
  const { login, isConfigured, loginAsDevStudent } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as { from?: Location })?.from?.pathname || '/dashboard';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const isSubmittingRef = useRef(false);

  // Restore remembered email on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(REMEMBER_EMAIL_KEY);
      if (saved) {
        setEmail(saved);
        setRememberMe(true);
      }
    } catch {
      // Ignore localStorage read errors
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmittingRef.current || isLoading) return; // Strict lock against duplicate submits

    setError(null);

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setError('Please enter your email address.');
      return;
    }
    if (!password) {
      setError('Please enter your password.');
      return;
    }

    isSubmittingRef.current = true;
    setIsLoading(true);

    try {
      // Handle Remember Me persistence
      if (rememberMe) {
        localStorage.setItem(REMEMBER_EMAIL_KEY, cleanEmail);
      } else {
        localStorage.removeItem(REMEMBER_EMAIL_KEY);
      }

      const err = await login(cleanEmail, password);

      if (err) {
        setError(err);
      } else {
        navigate(from, { replace: true });
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'An unexpected error occurred during sign in.';
      setError(message);
    } finally {
      isSubmittingRef.current = false;
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to your SkillProof AI account to continue."
    >
      {!isConfigured && (
        <div className="mb-6 space-y-3">
          <Alert
            variant="warning"
            message="Supabase credentials are not configured in frontend/.env. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to enable live authentication."
          />
          <button
            type="button"
            onClick={() => {
              loginAsDevStudent();
              navigate('/dashboard/student', { replace: true });
            }}
            className="w-full py-2.5 px-4 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-500/20 text-xs font-semibold flex items-center justify-center gap-2 transition"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>Continue as Demo Student (Local Dev Mode)</span>
          </button>
        </div>
      )}

      <div className="mb-6 p-3 rounded-xl bg-slate-800/40 border border-slate-700/60 flex items-center justify-between text-xs">
        <span className="text-slate-300">Testing or exploring?</span>
        <Link
          to="/"
          className="text-amber-400 hover:text-amber-300 font-semibold flex items-center space-x-1"
        >
          <Compass className="w-3.5 h-3.5 mr-1" />
          <span>Launch Guest Mode</span>
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      <form onSubmit={handleSubmit} noValidate className="space-y-5">
        {error && (
          <div className="space-y-2">
            <Alert variant="error" message={error} />
            {error.includes('Guest Mode') && (
              <button
                type="button"
                onClick={() => navigate('/')}
                className="w-full py-2 px-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 hover:bg-amber-500/20 text-xs font-semibold flex items-center justify-center gap-1.5 transition"
              >
                <Compass className="w-3.5 h-3.5" />
                <span>Continue Immediately in Guest Mode</span>
              </button>
            )}
          </div>
        )}

        {/* Email Address */}
        <Input
          label="Email address"
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="name@university.edu"
          autoComplete="email"
          required
          disabled={isLoading}
          leftIcon={<Mail className="w-4 h-4" />}
        />

        {/* Password with Show/Hide Toggle */}
        <div className="space-y-1.5">
          <Input
            label="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Enter your password"
            autoComplete="current-password"
            required
            disabled={isLoading}
            isPassword={true}
            leftIcon={<Lock className="w-4 h-4" />}
          />

          <div className="flex items-center justify-between pt-1">
            <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={e => setRememberMe(e.target.checked)}
                disabled={isLoading}
                className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-slate-900 transition"
              />
              <span>Remember me</span>
            </label>

            <Link
              to="/forgot-password"
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
            >
              Forgot password?
            </Link>
          </div>
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          fullWidth
          isLoading={isLoading}
          disabled={!isConfigured || isLoading}
          className="bg-gradient-to-r from-indigo-600 via-indigo-500 to-sky-500 hover:from-indigo-500 hover:to-sky-400 text-white font-semibold py-3 rounded-xl shadow-lg shadow-indigo-600/25 transition-all"
        >
          <span className="flex items-center justify-center gap-2">
            <span>Sign In</span>
            {!isLoading && <LogIn className="w-4 h-4" />}
          </span>
        </Button>
      </form>

      {/* Link to Registration */}
      <div className="mt-8 pt-6 border-t border-slate-800/80 text-center text-sm text-slate-400">
        Don&apos;t have an account?{' '}
        <Link
          to="/register"
          className="text-indigo-400 hover:text-indigo-300 font-semibold inline-flex items-center gap-1 transition-colors group"
        >
          <span>Create Account</span>
          <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
        </Link>
      </div>
    </AuthLayout>
  );
};
