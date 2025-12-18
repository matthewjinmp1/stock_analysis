#!/usr/bin/env python3
import os
import re

templates = ['peers.html', 'find_peers.html', 'adjusted_pe.html', 'ai_scores.html']

for template in templates:
    path = f'web_app/templates/{template}'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace hardcoded colors with CSS variables in common patterns
        # Table headers and cells
        content = re.sub(
            r'background:\s*linear-gradient\(135deg,\s*rgba\(125,\s*211,\s*252,\s*0\.2\)\s*0%,\s*rgba\(196,\s*181,\s*253,\s*0\.2\)\s*100%\);',
            'background: linear-gradient(135deg, rgba(from var(--accent-primary) r g b / 0.2) 0%, rgba(from var(--accent-secondary) r g b / 0.2) 100%);',
            content
        )

        content = re.sub(
            r'color:\s*#a5d8ff;',
            'color: var(--text-secondary);',
            content
        )

        content = re.sub(
            r'border-bottom:\s*1px solid rgba\(125,\s*211,\s*252,\s*0\.3\);',
            'border-bottom: 1px solid var(--border-color);',
            content
        )

        content = re.sub(
            r'text-shadow:\s*0 0 6px rgba\(125,\s*211,\s*252,\s*0\.3\);',
            'text-shadow: 0 0 6px var(--glow-primary);',
            content
        )

        content = re.sub(
            r'background:\s*rgba\(10,\s*10,\s*10,\s*0\.6\);',
            'background: var(--card-bg);',
            content
        )

        content = re.sub(
            r'border-bottom:\s*1px solid rgba\(125,\s*211,\s*252,\s*0\.1\);',
            'border-bottom: 1px solid rgba(from var(--border-color) r g b / 0.3);',
            content
        )

        # Score badge colors
        content = re.sub(
            r'background:\s*rgba\(34,\s*197,\s*94,\s*0\.2\);\s*color:\s*#4ade80;\s*border:\s*1px solid rgba\(34,\s*197,\s*94,\s*0\.4\);\s*box-shadow:\s*0 0 8px rgba\(34,\s*197,\s*94,\s*0\.2\);',
            'background: rgba(from var(--accent-success) r g b / 0.2);\n            color: var(--accent-success);\n            border: 1px solid rgba(from var(--accent-success) r g b / 0.4);\n            box-shadow: 0 0 8px rgba(from var(--accent-success) r g b / 0.2);',
            content
        )

        content = re.sub(
            r'background:\s*rgba\(239,\s*68,\s*68,\s*0\.2\);\s*color:\s*#f87171;\s*border:\s*1px solid rgba\(239,\s*68,\s*68,\s*0\.4\);\s*box-shadow:\s*0 0 8px rgba\(239,\s*68,\s*68,\s*0\.2\);',
            'background: rgba(from var(--accent-danger) r g b / 0.2);\n            color: var(--accent-danger);\n            border: 1px solid rgba(from var(--accent-danger) r g b / 0.4);\n            box-shadow: 0 0 8px rgba(from var(--accent-danger) r g b / 0.2);',
            content
        )

        # Company names and text colors
        content = re.sub(
            r'color:\s*#a5d8ff;\s*text-shadow:\s*0 0 8px rgba\(125,\s*211,\s*252,\s*0\.3\);',
            'color: var(--text-secondary);\n            text-shadow: 0 0 8px var(--glow-primary);',
            content
        )

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f'Updated colors in {template}')

print('All template colors updated to use CSS variables')