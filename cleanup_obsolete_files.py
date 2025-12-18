#!/usr/bin/env python3
"""
Cleanup script to remove obsolete files and directories.
Preserves the webapp and its dependencies.
"""
import os
import shutil
from pathlib import Path

# Files and directories to remove
OBSOLETE_FILES = [
    # Template-related scripts (obsolete since moved to React)
    'check_colors.py',
    'fix_colors.py',
    'final_color_fix.py',
    'simple_color_check.py',
    'cleanup_themes.py',
    'update_all_templates.py',
    'update_js.py',
    'update_css.py',
    'update_templates.py',

    # Migration-related files (used for database consolidation)
    'analyze_db_schemas.py',
    'migrate_to_normalized_db.py',
    'normalized_schema.sql',
    'test_refactored_system.py',

    # Old database files (replaced by new repository layer)
    'web_app/ui_cache_db.py',
    'web_app/watchlist_db.py',
    'web_app/adjusted_pe_db.py',
    'web_app/financial_scores_db.py',
    'web_app/peer_db.py',
    'web_app/peers_db.py',

    # Other obsolete files
    'backlog.txt',
    'web_app/RESTART_SERVER.md',
]

OBSOLETE_DIRECTORIES = [
    # Temp directory with debugging scripts
    'temp',
]

# Old database files that are now obsolete (in data directory)
OBSOLETE_DB_FILES = [
    'web_app/data/ui_cache.db',
    'web_app/data/ai_scores.db',
    'web_app/data/financial_scores.db',
    'web_app/data/adjusted_pe.db',
    'web_app/data/watchlist.db',
    'web_app/data/peers.db',
]

def cleanup_files():
    """Remove obsolete files."""
    print("Removing obsolete files...")
    removed_count = 0

    for file_path in OBSOLETE_FILES:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"  [REMOVED] {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"  [FAILED] {file_path}: {e}")
        else:
            print(f"  [SKIP] Already gone: {file_path}")

    return removed_count

def cleanup_directories():
    """Remove obsolete directories."""
    print("\nRemoving obsolete directories...")
    removed_count = 0

    for dir_path in OBSOLETE_DIRECTORIES:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"  [REMOVED] Directory: {dir_path}")
                removed_count += 1
            except Exception as e:
                print(f"  [FAILED] Directory {dir_path}: {e}")
        else:
            print(f"  [SKIP] Directory already gone: {dir_path}")

    return removed_count

def cleanup_old_databases():
    """Remove old database files that are now obsolete."""
    print("\nRemoving obsolete database files...")
    removed_count = 0

    for db_path in OBSOLETE_DB_FILES:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(f"  [REMOVED] Old database: {db_path}")
                removed_count += 1
            except Exception as e:
                print(f"  [FAILED] {db_path}: {e}")
        else:
            print(f"  [SKIP] Database already gone: {db_path}")

    return removed_count

def verify_important_files_remain():
    """Verify that important files and directories are still present."""
    print("\nVerifying important files remain...")

    important_paths = [
        'web_app/',  # Main webapp
        'web_app/repositories/',  # New architecture
        'web_app/services/',
        'web_app/controllers/',
        'web_app/app_new.py',  # New refactored app
        'AI_stock_scorer/',  # AI scoring (feeds webapp)
        'quantitative_stock_scorer/',  # Quantitative scoring (feeds webapp)
        'src/',  # Scraping infrastructure
        'tests/',  # Test infrastructure
        'config.example.py',  # Configuration template
        '.gitignore',  # Git ignore rules
    ]

    all_present = True
    for path in important_paths:
        if os.path.exists(path):
            print(f"  [OK] Present: {path}")
        else:
            print(f"  [MISSING] {path}")
            all_present = False

    return all_present

def show_final_stats():
    """Show final statistics about the codebase."""
    print("\nFinal codebase statistics:")

    total_files = 0
    total_dirs = 0

    for root, dirs, files in os.walk('.'):
        # Skip node_modules and other ignored directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
        total_files += len(files)
        total_dirs += len(dirs)

    print(f"  Total files: {total_files}")
    print(f"  Total directories: {total_dirs}")

    # Show main directories
    main_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.')]
    print(f"  Main directories: {', '.join(sorted(main_dirs))}")

def main():
    """Main cleanup function."""
    print("Codebase Cleanup for Webapp Preservation")
    print("=" * 50)
    print("This will remove obsolete files while preserving:")
    print("  [KEEP] web_app/ (refactored webapp)")
    print("  [KEEP] AI_stock_scorer/ (AI scoring system)")
    print("  [KEEP] quantitative_stock_scorer/ (quantitative analysis)")
    print("  [KEEP] src/ (scraping infrastructure)")
    print("  [KEEP] tests/ (test infrastructure)")
    print()

    # Confirm before proceeding
    response = input("Continue with cleanup? (yes/no): ").strip().lower()
    if response not in ['yes', 'y', 'true']:
        print("Cleanup cancelled.")
        return

    print("\nStarting cleanup...")

    # Perform cleanup
    files_removed = cleanup_files()
    dirs_removed = cleanup_directories()
    dbs_removed = cleanup_old_databases()

    total_removed = files_removed + dirs_removed + dbs_removed

    print(f"\n[SUCCESS] Cleanup completed!")
    print(f"   Files removed: {files_removed}")
    print(f"   Directories removed: {dirs_removed}")
    print(f"   Database files removed: {dbs_removed}")
    print(f"   Total items removed: {total_removed}")

    # Verify important files remain
    important_ok = verify_important_files_remain()

    if important_ok:
        print("\n[SUCCESS] All important files and directories preserved!")
    else:
        print("\n[WARNING] Some important files may be missing!")

    # Show final stats
    show_final_stats()

    print("\n[SUCCESS] Cleanup successful!")
    print("Your codebase is now cleaner and focused on the webapp and its dependencies.")
    print("Cursor AI should now work more efficiently with the reduced codebase size.")

if __name__ == '__main__':
    main()