#!/usr/bin/env python3
import os
import re

css_variables = '''
        /* CSS Custom Properties for Theming */
        :root {
            /* Default (Cyber) Theme Variables */
            --bg-primary: #0a0a0a;
            --bg-secondary: #0d0d0d;
            --bg-tertiary: #0a0a0a;
            --text-primary: #7dd3fc;
            --text-secondary: #a5d8ff;
            --text-muted: #7dd3fc;
            --accent-primary: #7dd3fc;
            --accent-secondary: #c4b5fd;
            --accent-success: #4ade80;
            --accent-danger: #f87171;
            --border-color: rgba(125, 211, 252, 0.3);
            --border-light: rgba(125, 211, 252, 0.4);
            --shadow-color: rgba(125, 211, 252, 0.15);
            --shadow-inset: rgba(125, 211, 252, 0.03);
            --glow-primary: rgba(125, 211, 252, 0.15);
            --glow-secondary: rgba(196, 181, 253, 0.3);
            --input-bg: #0a0a0a;
            --button-bg: rgba(125, 211, 252, 0.1);
            --card-bg: #0a0a0a;
            --header-bg: linear-gradient(135deg, #0a0a0a 0%, #1a0a1a 100%);
            --animation-glow: pulse-glow 4s ease-in-out infinite;
        }

        /* Light Theme Variables */
        body.light {
            --bg-primary: #ffffff;
            --bg-secondary: #f8f9fa;
            --bg-tertiary: #ffffff;
            --text-primary: #333333;
            --text-secondary: #666666;
            --text-muted: #6c757d;
            --accent-primary: #007bff;
            --accent-secondary: #0056b3;
            --accent-success: #28a745;
            --accent-danger: #dc3545;
            --border-color: #dee2e6;
            --border-light: #ced4da;
            --shadow-color: rgba(0, 0, 0, 0.1);
            --shadow-inset: rgba(255, 255, 255, 0.8);
            --glow-primary: rgba(0, 123, 255, 0.25);
            --glow-secondary: rgba(0, 123, 255, 0.3);
            --input-bg: #ffffff;
            --button-bg: rgba(0, 123, 255, 0.1);
            --card-bg: #f8f9fa;
            --header-bg: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            --animation-glow: none;
        }

        /* High Contrast Theme Variables */
        body.high-contrast {
            --bg-primary: #000000;
            --bg-secondary: #111111;
            --bg-tertiary: #000000;
            --text-primary: #ffffff;
            --text-secondary: #cccccc;
            --text-muted: #cccccc;
            --accent-primary: #ffffff;
            --accent-secondary: #ffffff;
            --accent-success: #ffffff;
            --accent-danger: #ff6666;
            --border-color: #ffffff;
            --border-light: #ffffff;
            --shadow-color: rgba(255, 255, 255, 0.1);
            --shadow-inset: rgba(255, 255, 255, 0.02);
            --glow-primary: rgba(255, 255, 255, 0.1);
            --glow-secondary: rgba(255, 255, 255, 0.3);
            --input-bg: #000000;
            --button-bg: #222222;
            --card-bg: #1a1a1a;
            --header-bg: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
            --animation-glow: pulse-glow 4s ease-in-out infinite;
        }
'''

templates = ['peers.html', 'find_peers.html', 'adjusted_pe.html', 'ai_scores.html']

for template in templates:
    path = f'web_app/templates/{template}'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Add CSS variables after the box-sizing rule
        pattern = r'(\*\s*\{\s*margin:\s*0;\s*padding:\s*0;\s*box-sizing:\s*border-box;\s*\})'
        content = re.sub(pattern, r'\1' + css_variables, content, flags=re.MULTILINE | re.DOTALL)

        # Update body background and color to use variables
        content = re.sub(
            r'background:\s*#0a0a0a;\s*background-image:[^;]+;\s*min-height:\s*100vh;\s*padding:\s*20px;\s*color:\s*#7dd3fc;',
            'background: var(--bg-primary);\n            background-image:\n                radial-gradient(circle at 20% 50%, rgba(0, 200, 220, 0.03) 0%, transparent 50%),\n                radial-gradient(circle at 80% 80%, rgba(200, 0, 200, 0.03) 0%, transparent 50%),\n                radial-gradient(circle at 40% 20%, rgba(120, 0, 200, 0.03) 0%, transparent 50%);\n            min-height: 100vh;\n            padding: 20px;\n            color: var(--text-primary);',
            content
        )

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f'Updated CSS variables in {template}')

print('All templates updated with CSS variables')