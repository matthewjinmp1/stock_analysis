#!/usr/bin/env python3
import os

templates = ['index.html', 'metrics.html', 'financial_metrics.html', 'peers.html', 'find_peers.html', 'adjusted_pe.html', 'ai_scores.html']

print("Checking for hardcoded colors in templates...")

for template in templates:
    path = f'web_app/templates/{template}'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        hardcoded_found = []

        for i, line in enumerate(lines):
            # Skip CSS variable definitions
            if '--' in line and ':' in line and line.strip().endswith(';'):
                continue

            # Look for hex colors and rgba values
            if ('#' in line and any(c in line for c in '0123456789abcdefABCDEF')) or 'rgba(' in line:
                # Simple check - if line contains color but not CSS variable
                if not line.strip().startswith('--') and not 'var(--' in line:
                    hardcoded_found.append(f"Line {i+1}: {line.strip()}")

        if hardcoded_found:
            print(f"\n=== {template} ===")
            for item in hardcoded_found[:10]:  # Show first 10
                print(item)

print("\nColor check complete.")


