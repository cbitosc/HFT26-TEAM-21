/**
 * ResetPasswordPage — allows setting a new password after clicking
 * the reset link from email. Supabase puts the token in the URL hash.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Lock, CheckCircle2, ArrowRight } from 'lucide-react';
import { AuthLayout } from '../components/AuthLayout';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { Alert } from '../components/Alert';
import { supabase, isSupabaseConfigured } from '../lib/supabase';

export const ResetPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSession, setHasSession] = useState(false);

  useEffect(() => {
    if (!isSupabaseConfigured) return;
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) setHasSession(true);
    });
    const { data: listener } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'PASSWORD_RECOVERY' || session) {
        setHasSession(true);
      }
    });
    return () => { listener.subscription.unsubscribe(); };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading) return;
    setError(null);

    if (password.length < 6) {
      setError('Password must contain at least 6 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsLoading(true);
    const { error: updateError } = await supabase.auth.updateUser({ password });
    setIsLoading(false);

    if (updateError) {
      setError(updateError.message || 'Could not update password. Please request a new reset link.');
    } else {
      setSuccess(true);
    }
  };

  if (success) {
    return (
      <AuthLayout title="Password updated" subtitle="Your account password has been reset successfully.">
        <div className="space-y-6 text-center">
          <Alert variant="success" message="Your password has been changed successfully. You can now sign in with your new credentials." />
          <Button
            fullWidth
            onClick={() => navigate('/login')}
            className="bg-gradient-to-r from-indigo-600 to-sky-500 hover:from-indigo-500 hover:to-sky-400 text-white font-semibold py-3 rounded-xl shadow-lg shadow-indigo-600/25 transition-all"
          >
            Go to Sign In
          </Button>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Set a new password" subtitle="Create a new, strong password for your SkillProof AI account.">
      {!hasSession && (
        <Alert
          variant="warning"
          message="No active recovery session detected. Please make sure you clicked the exact password reset link sent to your email."
          className="mb-6"
        />
      )}

      <form onSubmit={handleSubmit} noValidate className="space-y-5">
        {error && <Alert variant="error" message={error} />}

        <Input
          label="New password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder="Minimum 6 characters"
          autoComplete="new-password"
          required
          disabled={isLoading}
          isPassword={true}
          leftIcon={<Lock className="w-4 h-4" />}
        />

        <Input
          label="Confirm new password"
          value={confirmPassword}
          onChange={e => setConfirmPassword(e.target.value)}
          placeholder="Re-enter your new password"
          autoComplete="new-password"
          required
          disabled={isLoading}
          isPassword={true}
          leftIcon={<Lock className="w-4 h-4" />}
        />

        {password && confirmPassword && (
          <div className="flex items-center gap-1.5 text-xs">
            {password === confirmPassword ? (
              <span className="text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Passwords match
              </span>
            ) : (
              <span className="text-rose-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400 inline-block" />
                Passwords do not match
              </span>
            )}
          </div>
        )}

        <Button
          type="submit"
          fullWidth
          isLoading={isLoading}
          disabled={!hasSession || isLoading}
          className="bg-gradient-to-r from-indigo-600 to-sky-500 hover:from-indigo-500 hover:to-sky-400 text-white font-semibold py-3 rounded-xl shadow-lg shadow-indigo-600/25 transition-all mt-2"
        >
          <span className="flex items-center justify-center gap-2">
            <span>Update Password</span>
            {!isLoading && <ArrowRight className="w-4 h-4" />}
          </span>
        </Button>
      </form>

      <div className="mt-8 pt-6 border-t border-slate-800/80 text-center text-sm text-slate-400">
        <Link to="/login" className="text-indigo-400 hover:text-indigo-300 font-semibold transition-colors">
          Return to Sign In
        </Link>
      </div>
    </AuthLayout>
  );
};
