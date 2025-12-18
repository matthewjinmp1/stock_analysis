import React from 'react';
import { useTheme } from './ThemeContext';

interface LayoutProps {
  children: React.ReactNode;
  maxWidth?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, maxWidth = '800px' }) => {
  const { theme, setTheme } = useTheme();

  return (
    <div className="min-h-screen py-10 px-4">
      <div 
        className="mx-auto bg-bg-secondary rounded-[20px] border border-border-color shadow-[0_0_15px_var(--shadow-color),0_0_30px_var(--glow-primary),inset_0_0_15px_var(--shadow-inset)] overflow-visible animate-pulse-glow"
        style={{ maxWidth }}
      >
        {/* Theme Switcher */}
        <div className="flex justify-end gap-2.5 p-6 pb-0">
          <select 
            value={theme}
            onChange={(e) => setTheme(e.target.value as any)}
            className="p-2 px-3 text-[0.9em] bg-button-bg text-accent-primary border border-border-color rounded-lg cursor-pointer transition-all hover:opacity-80 focus:outline-none focus:border-accent-secondary focus:shadow-[0_0_15px_var(--glow-secondary)] font-sans min-w-[140px]"
          >
            <option value="dark">🌙 Cyber</option>
            <option value="light">☀️ Light</option>
            <option value="high-contrast">⚫ High Contrast</option>
          </select>
        </div>

        <main>{children}</main>
      </div>
    </div>
  );
};

export default Layout;
