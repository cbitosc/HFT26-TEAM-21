/**
 * RegisterPage — Premium SaaS registration page.
 *
 * Requirements:
 * - Role selection: Student | College Administrator | Recruiter (preserves existing roles and approval logic).
 * - Full name with User icon.
 * - Email address with Mail icon.
 * - Password with Lock icon and show/hide toggle.
 * - Confirm password with Lock icon and show/hide toggle.
 * - Client-side validation for email format, password matching, minimum length.
 * - Create Account button with loading state and duplicate submission prevention.
 * - Link to Login.
 * - Supabase email verification flow with dedicated confirmation view.
 */

import React, { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  User,
  Mail,
  Lock,
  UserPlus,
  ArrowRight,
  GraduationCap,
  Building2,
  Briefcase,
  MailCheck,
  CheckCircle2,
  Compass,
} from 'lucide-react';
import { AuthLayout } from '../components/AuthLayout';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { Alert } from '../components/Alert';
import { useAuth } from '../contexts/AuthContext';
import { clsx } from 'clsx';

type Role = 'student' | 'college_admin' | 'recruiter';

interface RoleOption {
  value: Role;
  label: string;
  badge: string;
  description: string;
  icon: React.ElementType;
}

const ROLES: RoleOption[] = [
  {
    value: 'student',
    label: 'Student',
    badge: 'Immediate Access',
    description: 'Solve coding challenges, upload portfolios, and earn verified skill proof.',
    icon: GraduationCap,
  },
  {
    value: 'college_admin',
    label: 'College Admin',
    badge: 'Requires Approval',
    description: 'Create custom assessments, assign cohorts, and monitor student metrics.',
    icon: Building2,
  },
  {
    value: 'recruiter',
    label: 'Recruiter',
    badge: 'Requires Approval',
    description: 'Discover verified candidates by demonstrated proof and host live interviews.',
    icon: Briefcase,
  },
];

export const RegisterPage: React.FC = () => {
  const { register, isConfigured } = useAuth();
  const navigate = useNavigate();

  const [role, setRole] = useState<Role>('student');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [registeredEmail, setRegisteredEmail] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const isSubmittingRef = useRef(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmittingRef.current || isLoading) return; // Strict lock against duplicate submits

    setError(null);

    // Form validation
    const cleanName = fullName.trim();
    const cleanEmail = email.trim().toLowerCase();

    if (!cleanName || cleanName.length < 2) {
      setError('Please provide your full legal name (minimum 2 characters).');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!cleanEmail || !emailRegex.test(cleanEmail)) {
      setError('Please provide a valid email address.');
      return;
    }

    if (password.length < 6) {
      setError('Password must contain at least 6 characters.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match. Please re-enter your confirmation password.');
      return;
    }

    isSubmittingRef.current = true;
    setIsLoading(true);

    try {
      const err = await register({
        email: cleanEmail,
        password,
        fullName: cleanName,
        role,
      });

      if (err) {
        setError(err);
      } else {
        setRegisteredEmail(cleanEmail);
        setSuccessMessage(
          role === 'student'
            ? 'Account created! A confirmation email has been sent by Supabase. Please verify your inbox to activate your account.'
            : 'Account registered! Your profile is pending administrative review. Please confirm your email to finalize registration.'
        );
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'An unexpected error occurred during account creation.';
      setError(message);
    } finally {
      isSubmittingRef.current = false;
      setIsLoading(false);
    }
  };

  // If successfully registered, show the email confirmation state
  if (successMessage) {
    return (
      <AuthLayout
        title="Check your email"
        subtitle="We dispatched a verification link to your inbox."
      >
        <div className="space-y-6 text-center">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto shadow-lg shadow-indigo-500/10">
            <MailCheck className="w-8 h-8 text-indigo-400" />
          </div>

          <div className="space-y-2">
            <p className="text-sm text-slate-300 font-medium">
              We sent an activation link to:
            </p>
            <p className="text-base font-semibold text-white bg-slate-800/60 py-2 px-4 rounded-xl border border-slate-700 font-mono inline-block">
              {registeredEmail}
            </p>
            <p className="text-xs text-slate-400 max-w-sm mx-auto leading-relaxed pt-2">
              Click the link in the message to verify your email address. Once verified, you can sign in directly to access your dashboard.
            </p>
          </div>

          <div className="pt-4 space-y-3">
            <Button
              variant="primary"
              fullWidth
              onClick={() => navigate('/login')}
              className="bg-gradient-to-r from-indigo-600 to-sky-500 hover:from-indigo-500 hover:to-sky-400 text-white font-semibold py-3 rounded-xl shadow-lg shadow-indigo-600/20"
            >
              Proceed to Sign In
            </Button>

            <p className="text-xs text-slate-500">
              Didn&apos;t receive the email? Check your spam folder or retry with another address.
            </p>
          </div>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Join SkillProof AI to verify and showcase your software engineering skills."
    >
      {!isConfigured && (
        <Alert
          variant="warning"
          message="Supabase is not yet configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in frontend/.env to enable live sign up."
          className="mb-6"
        />
      )}

      <div className="mb-6 p-3 rounded-xl bg-slate-800/40 border border-slate-700/60 flex items-center justify-between text-xs">
        <span className="text-slate-300">Want to explore first?</span>
        <Link
          to="/"
          className="text-amber-400 hover:text-amber-300 font-semibold flex items-center space-x-1"
        >
          <Compass className="w-3.5 h-3.5 mr-1" />
          <span>Launch Guest Demo</span>
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

        {/* Role Selector Tabs */}
        <div className="space-y-2">
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
            I am joining as a:
          </label>
          <div className="grid grid-cols-3 gap-2">
            {ROLES.map(r => {
              const Icon = r.icon;
              const isSelected = role === r.value;
              return (
                <button
                  key={r.value}
                  type="button"
                  onClick={() => setRole(r.value)}
                  className={clsx(
                    'p-2.5 rounded-xl border text-center transition-all flex flex-col items-center justify-center gap-1.5 focus:outline-none',
                    isSelected
                      ? 'border-indigo-500 bg-indigo-600/15 text-white ring-2 ring-indigo-500/30'
                      : 'border-slate-800 bg-slate-900/50 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                  )}
                >
                  <Icon className={clsx('w-4 h-4', isSelected ? 'text-indigo-400' : 'text-slate-500')} />
                  <span className="text-xs font-semibold leading-tight">{r.label}</span>
                </button>
              );
            })}
          </div>

          {/* Role disclaimer note */}
          {role !== 'student' && (
            <p className="text-[11px] text-amber-300/90 bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-lg flex items-center gap-1.5">
              <span>ⓘ</span>
              <span>Requires administrator approval prior to accessing institutional portal.</span>
            </p>
          )}
        </div>

        {/* Full Name */}
        <Input
          label="Full name"
          type="text"
          value={fullName}
          onChange={e => setFullName(e.target.value)}
          placeholder="Jane Doe"
          autoComplete="name"
          required
          disabled={isLoading}
          leftIcon={<User className="w-4 h-4" />}
        />

        {/* Email Address */}
        <Input
          label="Email address"
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="jane@university.edu"
          autoComplete="email"
          required
          disabled={isLoading}
          leftIcon={<Mail className="w-4 h-4" />}
        />

        {/* Password */}
        <Input
          label="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder="At least 6 characters"
          autoComplete="new-password"
          required
          disabled={isLoading}
          isPassword={true}
          leftIcon={<Lock className="w-4 h-4" />}
        />

        {/* Confirm Password */}
        <Input
          label="Confirm password"
          value={confirmPassword}
          onChange={e => setConfirmPassword(e.target.value)}
          placeholder="Re-enter your password"
          autoComplete="new-password"
          required
          disabled={isLoading}
          isPassword={true}
          leftIcon={<Lock className="w-4 h-4" />}
        />

        {/* Password Match Indicator / Help */}
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

        {/* Submit Button */}
        <Button
          type="submit"
          fullWidth
          isLoading={isLoading}
          disabled={!isConfigured || isLoading}
          className="bg-gradient-to-r from-indigo-600 via-indigo-500 to-sky-500 hover:from-indigo-500 hover:to-sky-400 text-white font-semibold py-3 rounded-xl shadow-lg shadow-indigo-600/25 transition-all mt-2"
        >
          <span className="flex items-center justify-center gap-2">
            <span>Create Account</span>
            {!isLoading && <UserPlus className="w-4 h-4" />}
          </span>
        </Button>
      </form>

      {/* Link to Login */}
      <div className="mt-8 pt-6 border-t border-slate-800/80 text-center text-sm text-slate-400">
        Already have an account?{' '}
        <Link
          to="/login"
          className="text-indigo-400 hover:text-indigo-300 font-semibold inline-flex items-center gap-1 transition-colors group"
        >
          <span>Sign In</span>
          <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
        </Link>
      </div>
    </AuthLayout>
  );
};
