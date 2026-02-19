#!/usr/bin/env python3
"""
Script to remove AI-generated comments from Python files.

This script recursively processes all .py files in a directory tree and removes
comments that contain phrases indicating AI code generation. Docstrings and
regular code are preserved.

Usage:
    python clean_ai_comments.py [path] [--dry-run]

Arguments:
    path        Directory to process (default: current directory)
    --dry-run   Show changes without modifying files
"""

import argparse
import os
import re
import sys
import tokenize
import io
from pathlib import Path
from typing import List, Tuple


# AI-related phrases to detect in comments (case-insensitive)
AI_PATTERNS = [
    r'generated\s+by',
    r'written\s+by',
    r'created\s+by',
    r'auto-generated',
    r'ai-generated',
    r'this\s+file\s+was',
    r'this\s+code\s+was',
    r'generated\s+with',
    r'generated\s+using',
    r'created\s+with',
    r'written\s+with',
    r'\bby\s+ai\b',
    r'\busing\s+ai\b',
    r'ai\s+assisted',
    r'ai\s+generated',
    r'generated\s+automatically',
]

# Compile patterns for efficiency
AI_REGEX = re.compile('|'.join(AI_PATTERNS), re.IGNORECASE)

# Directories to skip during traversal
SKIP_DIRS = {
    '.git',
    '.venv',
    'venv',
    '__pycache__',
    '.pytest_cache',
    '.qodo',
    '.roo',
    '.vscode',
    'node_modules',
    '.eggs',
    '*.egg-info',
}


def is_ai_comment(comment_text: str) -> bool:
    """
    Check if a comment contains AI-generated phrases.
    
    Args:
        comment_text: The comment text (including the # symbol).
    
    Returns:
        True if the comment contains AI-related phrases, False otherwise.
    """
    # Remove the leading # and whitespace for checking
    text = comment_text.lstrip('#').strip()
    return bool(AI_REGEX.search(text))


def process_file(filepath: Path, dry_run: bool = False) -> Tuple[bool, int]:
    """
    Process a single Python file, removing AI-generated comments.
    
    Args:
        filepath: Path to the Python file.
        dry_run: If True, only report changes without writing.
    
    Returns:
        Tuple of (success, removed_count) where:
            - success: True if processing completed without errors
            - removed_count: Number of AI comments removed
    """
    removed_count = 0
    
    try:
        # Read file content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (IOError, OSError) as e:
        print(f"  ⚠️  Warning: Could not read {filepath}: {e}")
        return False, 0
    except UnicodeDecodeError as e:
        print(f"  ⚠️  Warning: Could not decode {filepath}: {e}")
        return False, 0
    
    try:
        # Tokenize the content
        tokens = list(tokenize.generate_tokens(io.StringIO(content).readline))
    except tokenize.TokenError as e:
        print(f"  ⚠️  Warning: Tokenization error in {filepath}: {e}")
        return False, 0
    
    # Filter out AI-generated comments
    filtered_tokens = []
    for token in tokens:
        if token.type == tokenize.COMMENT:
            if is_ai_comment(token.string):
                removed_count += 1
                # Skip this comment (don't add to filtered_tokens)
                continue
        filtered_tokens.append(token)
    
    # If no changes, return early
    if removed_count == 0:
        return True, 0
    
    # Reconstruct the code from tokens
    try:
        new_content = tokenize.untokenize(filtered_tokens)
    except Exception as e:
        print(f"  ⚠️  Warning: Could not reconstruct code for {filepath}: {e}")
        return False, 0
    
    # Write the modified content back
    if not dry_run:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except (IOError, OSError) as e:
            print(f"  ⚠️  Warning: Could not write {filepath}: {e}")
            return False, removed_count
    
    return True, removed_count


def should_skip_directory(dirpath: Path) -> bool:
    """
    Check if a directory should be skipped during traversal.
    
    Args:
        dirpath: Path to the directory.
    
    Returns:
        True if the directory should be skipped, False otherwise.
    """
    # Check if any part of the path matches skip patterns
    for part in dirpath.parts:
        if part in SKIP_DIRS:
            return True
        # Handle glob patterns like *.egg-info
        if part.endswith('.egg-info'):
            return True
    return False


def find_python_files(root_dir: Path) -> List[Path]:
    """
    Recursively find all Python files in a directory tree.
    
    Args:
        root_dir: Root directory to search.
    
    Returns:
        List of paths to Python files.
    """
    python_files = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        current_path = Path(dirpath)
        
        # Skip ignored directories (modify dirnames in-place to prevent descent)
        dirnames[:] = [d for d in dirnames if not should_skip_directory(current_path / d)]
        
        # Find Python files
        for filename in filenames:
            if filename.endswith('.py'):
                python_files.append(current_path / filename)
    
    return python_files


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Remove AI-generated comments from Python files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                     # Process current directory
  %(prog)s /path/to/project    # Process specific directory
  %(prog)s --dry-run           # Preview changes without modifying files
        """
    )
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Directory to process (default: current directory)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show changes without modifying files'
    )
    
    args = parser.parse_args()
    
    root_dir = Path(args.path).resolve()
    
    if not root_dir.exists():
        print(f"Error: Directory does not exist: {root_dir}")
        sys.exit(1)
    
    if not root_dir.is_dir():
        print(f"Error: Not a directory: {root_dir}")
        sys.exit(1)
    
    print(f"🔍 Scanning for Python files in: {root_dir}")
    
    # Find all Python files
    python_files = find_python_files(root_dir)
    
    if not python_files:
        print("No Python files found.")
        sys.exit(0)
    
    print(f"📄 Found {len(python_files)} Python file(s)")
    print()
    
    # Process each file
    total_removed = 0
    processed_count = 0
    error_count = 0
    modified_files = []
    
    for filepath in python_files:
        success, removed = process_file(filepath, dry_run=args.dry_run)
        
        if success:
            processed_count += 1
            if removed > 0:
                total_removed += removed
                mode = "Would clean" if args.dry_run else "Cleaned"
                print(f"  ✓ {mode}: {filepath.relative_to(root_dir)} ({removed} comment(s))")
                modified_files.append(filepath)
        else:
            error_count += 1
    
    # Print summary
    print()
    print("=" * 60)
    print("📊 Summary:")
    print(f"   Files processed: {processed_count}")
    print(f"   Comments removed: {total_removed}")
    if error_count > 0:
        print(f"   Errors: {error_count}")
    
    if args.dry_run and total_removed > 0:
        print()
        print("⚠️  This was a dry run. No files were modified.")
        print("   Run without --dry-run to apply changes.")
    elif total_removed == 0:
        print()
        print("✅ No AI-generated comments found. Code is clean!")
    
    print("=" * 60)


if __name__ == '__main__':
    main()
