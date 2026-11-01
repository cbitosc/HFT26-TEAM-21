/**
 * Supabase client initialisation.
 * Uses VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY from the environment.
 * The service_role key is NEVER used or stored on the frontend.
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn(
    '[SkillProof AI] Supabase environment variables are not configured. ' +
    'Authentication features will not be available. ' +
    'Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in frontend/.env'
  );
}

/**
 * Configured Supabase client.
 * Uses the anon/public key — all access is subject to Row Level Security policies.
 */
export const supabase: SupabaseClient = createClient(
  supabaseUrl || 'https://placeholder.supabase.co',
  supabaseAnonKey || 'placeholder-anon-key',
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  }
);

/** True when Supabase credentials are present in the environment. */
export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);
