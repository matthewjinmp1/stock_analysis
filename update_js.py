#!/usr/bin/env python3
import os
import re

templates = ['peers.html', 'find_peers.html', 'adjusted_pe.html', 'ai_scores.html', 'financial_metrics.html']

for template in templates:
    path = f'web_app/templates/{template}'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace the setTheme function
        old_js = r'function setTheme\(theme\) \{\s*const body = document\.body;\s*const darkBtn = document\.getElementById\(\'darkThemeBtn\'\);\s*const highContrastBtn = document\.getElementById\(\'highContrastThemeBtn\'\);\s*// Remove existing theme classes\s*body\.classList\.remove\(\'high-contrast\'\);\s*// Add new theme class if needed\s*if \(theme === \'high-contrast\'\) \{\s*body\.classList\.add\(\'high-contrast\'\);\s*\}\s*// Update button states\s*darkBtn\.classList\.toggle\(\'active\', theme === \'dark\'\);\s*highContrastBtn\.classList\.toggle\(\'active\', theme === \'high-contrast\'\);\s*// Save preference to localStorage\s*localStorage\.setItem\(\'theme\', theme\);\s*\}'

        new_js = '''function setTheme(theme) {
            const body = document.body;
            const themeSelect = document.getElementById('themeSelect');

            // Remove existing theme classes
            body.classList.remove('high-contrast');
            body.classList.remove('light');

            // Add new theme class if needed
            if (theme === 'high-contrast') {
                body.classList.add('high-contrast');
            } else if (theme === 'light') {
                body.classList.add('light');
            }

            // Update dropdown selection
            themeSelect.value = theme;

            // Save preference to localStorage
            localStorage.setItem('theme', theme);
        }'''

        content = re.sub(old_js, new_js, content, flags=re.MULTILINE | re.DOTALL)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f'Updated JavaScript in {template}')

print('All template JavaScript updated')