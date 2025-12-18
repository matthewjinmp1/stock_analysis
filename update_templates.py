#!/usr/bin/env python3
import os
import re

templates = ['peers.html', 'find_peers.html', 'adjusted_pe.html', 'ai_scores.html']

for template in templates:
    path = f'web_app/templates/{template}'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace theme-button with theme-dropdown in HTML
        pattern = r'<button class="theme-button[^"]*"[^>]*>🌙 Cyber</button>\s*<button class="theme-button[^"]*"[^>]*>⚫ High Contrast</button>'
        replacement = '''<select class="theme-dropdown" id="themeSelect" onchange="setTheme(this.value)">
                <option value="dark">🌙 Cyber</option>
                <option value="light">☀️ Light</option>
                <option value="high-contrast">⚫ High Contrast</option>
            </select>'''

        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f'Updated {template}')

print('All templates updated with theme dropdown')