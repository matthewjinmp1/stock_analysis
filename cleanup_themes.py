#!/usr/bin/env python3
import os
import re

templates = ['financial_metrics.html', 'peers.html', 'find_peers.html', 'adjusted_pe.html', 'ai_scores.html']

for template in templates:
    path = f'web_app/templates/{template}'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove all body.high-contrast theme override sections
        # Find and remove sections that start with body.high-contrast and end before the next major CSS rule
        lines = content.split('\n')
        new_lines = []
        skip_mode = False

        for i, line in enumerate(lines):
            # Start skipping when we encounter a body.high-contrast rule
            if re.match(r'^\s*body\.high-contrast\s*\{', line) or re.match(r'^\s*body\.high-contrast\s+\.', line):
                skip_mode = True
                continue

            # Stop skipping when we encounter a new CSS rule that's not high-contrast
            if skip_mode:
                # Check if this line starts a new CSS rule
                if re.match(r'^\s*\w+.*\{', line) and not line.strip().startswith('body.high-contrast'):
                    skip_mode = False
                else:
                    continue

            new_lines.append(line)

        content = '\n'.join(new_lines)

        # Also remove any remaining theme-button references
        content = re.sub(r'body\.high-contrast \.theme-button.*?\n.*?\{.*?\}', '', content, flags=re.MULTILINE | re.DOTALL)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f'Cleaned theme overrides from {template}')

print('All templates cleaned of old theme overrides')