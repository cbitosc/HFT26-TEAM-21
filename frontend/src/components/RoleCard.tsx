import React from 'react';
import { LucideIcon, ArrowRight, Lock } from 'lucide-react';

interface RoleCardProps {
  title: string;
  role: string;
  description: string;
  icon: LucideIcon;
  features: string[];
  accentColor: string;
}

export const RoleCard: React.FC<RoleCardProps> = ({
  title,
  role,
  description,
  icon: Icon,
  features,
  accentColor,
}) => {
  return (
    <div className="relative group rounded-2xl border border-slate-800 bg-slate-900/50 hover:bg-slate-900/80 p-6 flex flex-col justify-between transition-all duration-200 hover:border-slate-700 hover:shadow-xl hover:shadow-slate-950/50">
      <div>
        {/* Role Header */}
        <div className="flex items-center justify-between mb-4">
          <div
            className={`w-12 h-12 rounded-xl flex items-center justify-center border ${accentColor}`}
          >
            <Icon className="w-6 h-6" />
          </div>
          <span className="inline-flex items-center space-x-1 text-[11px] font-medium text-slate-400 bg-slate-800/80 border border-slate-700/60 px-2 py-0.5 rounded-full">
            <Lock className="w-3 h-3 text-slate-500" />
            <span>Module 2 Planned</span>
          </span>
        </div>

        <div className="mb-2">
          <span className="text-xs font-semibold tracking-wider uppercase text-sky-400">
            {role}
          </span>
          <h3 className="text-xl font-bold text-white tracking-tight mt-0.5">
            {title}
          </h3>
        </div>

        <p className="text-sm text-slate-300 leading-relaxed mb-6">
          {description}
        </p>

        {/* Planned Capabilities */}
        <div className="space-y-2 mb-6">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Planned Capabilities:
          </p>
          <ul className="space-y-1.5">
            {features.map((feature, idx) => (
              <li key={idx} className="flex items-start text-xs text-slate-300">
                <span className="text-sky-400 mr-2 font-bold">•</span>
                <span>{feature}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Placeholder CTA */}
      <div className="pt-4 border-t border-slate-800/80">
        <button
          disabled
          className="w-full inline-flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700 cursor-not-allowed group-hover:border-slate-600 transition-colors"
        >
          <span>Available in Module 2</span>
          <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
        </button>
      </div>
    </div>
  );
};
