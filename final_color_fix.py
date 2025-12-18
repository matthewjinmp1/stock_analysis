#!/usr/bin/env python3
import os
import re

templates = ['metrics.html', 'financial_metrics.html', 'peers.html', 'find_peers.html', 'adjusted_pe.html', 'ai_scores.html']

for template in templates:
    path = f'web_app/templates/{template}'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix body background gradients to use CSS variables
        content = re.sub(
            r'(\s+)background:\s*#[0-9a-fA-F]{3,6};\s*background-image:\s*r radial-gradient[^;]+;',
            r'\1background: var(--bg-primary);\n\1background-image: var(--bg-gradient);',
            content
        )

        # Fix remaining text colors
        content = re.sub(
            r'color:\s*#ffffff;',
            'color: var(--text-primary);',
            content
        )

        content = re.sub(
            r'color:\s*#cccccc;',
            'color: var(--text-secondary);',
            content
        )

        # Fix text shadows
        content = re.sub(
            r'text-shadow:\s*0 0 8px rgba\(196,\s*181,\s*253,\s*0\.3\);',
            'text-shadow: 0 0 8px var(--glow-secondary);',
            content
        )

        # Fix remaining rgba colors
        content = re.sub(
            r'background:\s*rgba\(251,\s*191,\s*36,\s*0\.2\);\s*color:\s*#fbbf24;\s*border:\s*1px solid rgba\(251,\s*191,\s*36,\s*0\.4\);\s*box-shadow:\s*0 0 8px rgba\(251,\s*191,\s*36,\s*0\.2\);',
            'background: rgba(from var(--accent-warning) r g b / 0.2);\n            color: var(--accent-warning);\n            border: 1px solid rgba(from var(--accent-warning) r g b / 0.4);\n            box-shadow: 0 0 8px rgba(from var(--accent-warning) r g b / 0.2);',
            content
        )

        # Fix remaining button and UI element colors
        content = re.sub(
            r'color:\s*#7dd3fc;',
            'color: var(--text-primary);',
            content
        )

        content = re.sub(
            r'background:\s*rgba\(125,\s*211,\s*252,\s*0\.2\);',
            'background: var(--button-bg);',
            content
        )

        content = re.sub(
            r'border-color:\s*rgba\(125,\s*211,\s*252,\s*0\.5\);',
            'border-color: var(--accent-primary);',
            content
        )

        content = re.sub(
            r'box-shadow:\s*0 0 8px rgba\(125,\s*211,\s*252,\s*0\.3\);',
            'box-shadow: 0 0 8px var(--glow-primary);',
            content
        )

        content = re.sub(
            r'border:\s*1px solid rgba\(125,\s*211,\s*252,\s*0\.4\);',
            'border: 1px solid var(--border-light);',
            content
        )

        content = re.sub(
            r'box-shadow:\s*0 0 12px rgba\(125,\s*211,\s*252,\s*0\.3\);',
            'box-shadow: 0 0 12px var(--glow-primary);',
            content
        )

        content = re.sub(
            r'box-shadow:\s*0 0 10px rgba\(125,\s*211,\s*252,\s*0\.2\);',
            'box-shadow: 0 0 10px var(--glow-primary);',
            content
        )

        content = re.sub(
            r'border-top:\s*1px solid rgba\(125,\s*211,\s*252,\s*0\.1\);',
            'border-top: 1px solid rgba(from var(--border-color) r g b / 0.3);',
            content
        )

        content = re.sub(
            r'border:\s*1px solid rgba\(125,\s*211,\s*252,\s*0\.2\);',
            'border: 1px solid var(--border-color);',
            content
        )

        # Fix the label color in adjusted_pe.html
        content = re.sub(
            r'color:\s*rgba\(125,\s*211,\s*252,\s*0\.8\);',
            'color: var(--text-secondary);',
            content
        )

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f'Final color fixes applied to {template}')

print('All final color fixes completed')





