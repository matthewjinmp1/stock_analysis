#!/usr/bin/env python3
import os
import re

templates = ['index.html', 'metrics.html', 'financial_metrics.html', 'peers.html', 'find_peers.html', 'adjusted_pe.html', 'ai_scores.html']

for template in templates:
    path = f'web_app/templates/{template}'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find hardcoded colors that are NOT in CSS variable definitions
        # Look for hex colors and rgba values that are not in --variable definitions
        color_pattern = r'(?<!--[^:]*:)[^/]*#[0-9a-fA-F]{3,6}[^;]*;?'
        rgba_pattern = r'(?<!--[^:]*:)[^/]*rgba\([^)]+\)[^;]*;?'

        hex_matches = re.findall(color_pattern, content)
        rgba_matches = re.findall(rgba_pattern, content)

        if hex_matches or rgba_matches:
            print(f"\n=== {template} ===")
            if hex_matches:
                print("Hex colors found:")
                for match in hex_matches[:5]:  # Show first 5
                    if match.strip() and not match.startswith('//'):
                        print(f"  {match.strip()}")
            if rgba_matches:
                print("RGBA colors found:")
                for match in rgba_matches[:5]:  # Show first 5
                    if match.strip() and not match.startswith('//'):
                        print(f"  {match.strip()}")

print("\nColor check complete.")