/**
 * DashboardLayout — wraps role dashboards with the Navbar and Footer,
 * providing a consistent shell for authenticated pages.
 */

import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { Footer } from '../components/Footer';
import { GuestDemoBanner } from '../components/GuestDemoBanner';

export const DashboardLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-sky-500 selection:text-white">
      <div>
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <GuestDemoBanner />
          <Outlet />
        </main>
      </div>
      <Footer />
    </div>
  );
};
