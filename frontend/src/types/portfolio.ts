/**
 * TypeScript types for Student Portfolio (Module 3).
 */

export interface ProjectItem {
  name: string;
  description: string;
  technologies: string[];
}

export interface SkillsStructure {
  programming_languages: string[];
  frameworks_and_tools: string[];
}

export interface PortfolioStructure {
  projects: ProjectItem[];
  skills: SkillsStructure;
  domains: string[];
  dsa_topics: string[];
}

export interface PortfolioResponse {
  id?: string;
  user_id: string;
  confirmed: boolean;
  confirmed_at?: string | null;
  skills_status: 'unverified' | 'partially_verified' | 'verified';
  data: PortfolioStructure;
  raw_filename?: string | null;
  file_type?: string | null;
  created_at?: string;
  updated_at?: string;
}
