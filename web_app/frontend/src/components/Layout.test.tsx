import { render, screen, fireEvent } from '@testing-library/react';
import Layout from './Layout';
import { ThemeProvider } from './ThemeContext';
import { describe, it, expect } from 'vitest';
import React from 'react';

describe('Layout Component', () => {
  it('renders children correctly', () => {
    render(
      <ThemeProvider>
        <Layout>
          <div data-testid="child">Test Child</div>
        </Layout>
      </ThemeProvider>
    );
    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('allows changing themes via select', () => {
    render(
      <ThemeProvider>
        <Layout>
          <div>Content</div>
        </Layout>
      </ThemeProvider>
    );

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'light' } });
    
    expect(select).toHaveValue('light');
    expect(document.body.classList.contains('light')).toBe(true);
  });

  it('applies custom maxWidth', () => {
    const { container } = render(
      <ThemeProvider>
        <Layout maxWidth="1000px">
          <div>Content</div>
        </Layout>
      </ThemeProvider>
    );

    // The inner container should have the style
    const mainContainer = container.querySelector('[style*="max-width: 1000px"]');
    expect(mainContainer).toBeInTheDocument();
  });
});
