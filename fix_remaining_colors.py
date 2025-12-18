#!/usr/bin/env python3
import os
import re

templates = ['metrics.html', 'financial_metrics.html', 'peers.html', 'find_peers.html', 'adjusted_pe.html', 'ai_scores.html']

for template in templates:
    path = f'web_app/templates/{template}'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace table hover backgrounds
        content = re.sub(
            r'background:\s*rgba\(125,\s*211,\s*252,\s*0\.05\);',
            'background: var(--table-hover-bg);',
            content
        )

        # Replace text colors
        content = re.sub(
            r'color:\s*#a5d8ff;',
            'color: var(--text-secondary);',
            content
        )

        content = re.sub(
            r'color:\s*rgba\(125,\s*211,\s*252,\s*0\.7\);',
            'color: var(--text-muted);',
            content
        )

        content = re.sub(
            r'color:\s*rgba\(125,\s*211,\s*252,\s*0\.6\);',
            'color: var(--text-muted);',
            content
        )

        content = re.sub(
            r'color:\s*#f87171;',
            'color: var(--accent-danger);',
            content
        )

        # Replace background colors
        content = re.sub(
            r'background:\s*rgba\(13,\s*13,\s*13,\s*0\.8\);',
            'background: var(--card-bg);',
            content
        )

        content = re.sub(
            r'background:\s*rgba\(10,\s*10,\s*10,\s*0\.6\);',
            'background: var(--card-bg);',
            content
        )

        # Replace border colors
        content = re.sub(
            r'border:\s*1px solid rgba\(125,\s*211,\s*252,\s*0\.3\);',
            'border: 1px solid var(--border-color);',
            content
        )

        # Replace shadow colors
        content = re.sub(
            r'box-shadow:\s*0 0 15px rgba\(125,\s*211,\s*252,\s*0\.15\);',
            'box-shadow: 0 0 15px var(--shadow-color);',
            content
        )

        # Replace text shadows
        content = re.sub(
            r'text-shadow:\s*0 0 8px rgba\(125,\s*211,\s*252,\s*0\.3\);',
            'text-shadow: 0 0 8px var(--glow-primary);',
            content
        )

        # Replace specific table header backgrounds
        content = re.sub(
            r'background:\s*linear-gradient\(135deg,\s*rgba\(125,\s*211,\s*252,\s*0\.2\)\s*0%,\s*rgba\(196,\s*181,\s*253,\s*0\.2\)\s*100%\);',
            'background: linear-gradient(135deg, rgba(from var(--accent-primary) r g b / 0.2) 0%, rgba(from var(--accent-secondary) r g b / 0.2) 100%);',
            content
        )

        # Replace button backgrounds
        content = re.sub(
            r'background:\s*rgba\(125,\s*211,\s*252,\s*0\.1\);',
            'background: var(--button-bg);',
            content
        )

        # Replace specific rgba colors
        content = re.sub(
            r'background:\s*rgba\(196,\s*181,\s*253,\s*0\.15\) !important;',
            'background: rgba(from var(--accent-secondary) r g b / 0.15) !important;',
            content
        )

        content = re.sub(
            r'color:\s*#c4b5fd;',
            'color: var(--accent-secondary);',
            content
        )

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f'Fixed remaining colors in {template}')

print('All remaining hardcoded colors replaced with CSS variables')





