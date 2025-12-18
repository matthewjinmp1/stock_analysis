import React from 'react';
import { useTheme } from './ThemeContext';

interface LayoutProps {
  children: React.ReactNode;
  maxWidth?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, maxWidth = '800px' }) => {
  const { theme, setTheme } = useTheme();

  // Convert pixel maxWidth to Tailwind class if possible, or use style
  const containerStyle = { maxWidth: maxWidth };

  return (
    <div className="min-h-screen py-10 px-4 text-text-primary bg-bg-primary flex flex-col items-center">
      <div 
        className="w-full bg-bg-secondary rounded-[20px] border border-border-color shadow-xl overflow-hidden animate-pulse-glow"
        style={containerStyle}
      >
        {/* Theme Switcher */}
        <div className="flex justify-end gap-2.5 p-4 bg-bg-tertiary border-b border-border-color">
          <select 
            value={theme}
            onChange={(e) => setTheme(e.target.value as any)}
            className="p-2 px-3 text-[0.9em] bg-button-bg text-text-secondary border border-border-color rounded-lg cursor-pointer transition-all hover:opacity-80 focus:outline-none focus:border-accent-secondary font-sans min-w-[140px]"
          >
            <option value="dark">🌙 Cyber</option>
            <option value="light">☀️ Light</option>
            <option value="high-contrast">⚫ High Contrast</option>
          </select>
        </div>

        <main className="w-full flex flex-col">{children}</main>
      </div>
    </div>
  );
};

export default Layout;
