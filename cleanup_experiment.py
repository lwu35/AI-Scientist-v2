#!/usr/bin/env python3
"""
Cleanup script for AI Scientist experiments
Removes generated files that could cause issues in subsequent runs
while preserving valuable experimental data and citations.
"""

import os
import sys
import shutil
import glob
import argparse

def cleanup_experiment(experiment_dir, verbose=True, regenerate_citations=False):
    """Clean up an experiment directory for re-run"""
    
    if not os.path.exists(experiment_dir):
        print(f"❌ Experiment directory not found: {experiment_dir}")
        return False
    
    print(f"🧹 Cleaning experiment: {experiment_dir}")
    
    # Files to remove
    cleanup_patterns = [
        # LaTeX auxiliary files (can cause stale references)
        "latex/*.aux",
        "latex/*.bbl", 
        "latex/*.blg",
        "latex/*.log",
        "latex/*.out",
        "latex/*.fls",
        "latex/*.fdb_latexmk",
        "latex/*.synctex.gz",
        
        # Bibliography files (will be regenerated from cached_citations.bib)
        "latex/references.bib",
        
        # Generated PDFs (will be regenerated with fixes)
        "*.pdf",
        
        # Corrupted templates (will be regenerated)
        "latex/template.tex",
        
        # Reflection artifacts (will be regenerated)
        "*_reflection*_imgs",
    ]
    
    # Optionally remove citation cache to force complete regeneration
    if regenerate_citations:
        cleanup_patterns.extend([
            "cached_citations.bib",
            "citations_progress.json",
        ])
    
    # Directories to remove
    cleanup_dirs = [
        # Reflection image directories
        "*_reflection*_imgs",
    ]
    
    files_removed = 0
    dirs_removed = 0
    
    # Remove files matching patterns
    for pattern in cleanup_patterns:
        full_pattern = os.path.join(experiment_dir, pattern)
        matches = glob.glob(full_pattern)
        for match in matches:
            if os.path.isfile(match):
                if verbose:
                    print(f"  🗑️  Removing file: {os.path.relpath(match, experiment_dir)}")
                os.remove(match)
                files_removed += 1
    
    # Remove directories matching patterns
    for pattern in cleanup_dirs:
        full_pattern = os.path.join(experiment_dir, pattern)
        matches = glob.glob(full_pattern)
        for match in matches:
            if os.path.isdir(match):
                if verbose:
                    print(f"  🗑️  Removing directory: {os.path.relpath(match, experiment_dir)}")
                shutil.rmtree(match)
                dirs_removed += 1
    
    print(f"✅ Cleanup complete: {files_removed} files, {dirs_removed} directories removed")
    
    if regenerate_citations:
        print("🔄 Citation cache removed - citations will be completely regenerated")
    else:
        print("💾 Citation cache preserved - references.bib will be regenerated from cached_citations.bib")
    
    # Show what's preserved
    if verbose:
        print(f"\n📋 Preserved important files:")
        preserved_items = [
            "idea.json", "idea.md",
            "figures/", "data/", "logs/",
            "latex/*.sty", "latex/*.bst", "latex/*.cls"
        ]
        
        if not regenerate_citations:
            preserved_items.append("cached_citations.bib")  # Citations cache (references.bib will be regenerated from this)
        for item in preserved_items:
            full_path = os.path.join(experiment_dir, item)
            if '*' in item:
                matches = glob.glob(full_path)
                if matches:
                    print(f"  ✅ {item} ({len(matches)} files)")
            elif os.path.exists(full_path):
                print(f"  ✅ {item}")
    
    return True

def find_experiments():
    """Find all experiment directories"""
    experiment_dirs = []
    if os.path.exists("experiments"):
        for item in os.listdir("experiments"):
            item_path = os.path.join("experiments", item)
            if os.path.isdir(item_path) and item.startswith("2025-"):
                experiment_dirs.append(item_path)
    return sorted(experiment_dirs)

def main():
    parser = argparse.ArgumentParser(description="Clean up AI Scientist experiment directories")
    parser.add_argument("experiment_dir", nargs="?", help="Specific experiment directory to clean")
    parser.add_argument("--all", action="store_true", help="Clean all experiment directories")
    parser.add_argument("--list", action="store_true", help="List available experiment directories")
    parser.add_argument("--quiet", "-q", action="store_true", help="Reduce output verbosity")
    parser.add_argument("--regenerate-citations", action="store_true", help="Also remove citation cache to force complete regeneration")
    
    args = parser.parse_args()
    
    if args.list:
        experiments = find_experiments()
        if experiments:
            print("📁 Available experiment directories:")
            for exp in experiments:
                print(f"  - {exp}")
        else:
            print("No experiment directories found.")
        return
    
    if args.all:
        experiments = find_experiments()
        if not experiments:
            print("No experiment directories found.")
            return
        
        print(f"🧹 Cleaning {len(experiments)} experiment directories...")
        success_count = 0
        for exp_dir in experiments:
            if cleanup_experiment(exp_dir, verbose=not args.quiet, regenerate_citations=args.regenerate_citations):
                success_count += 1
            print()  # Empty line between experiments
        
        print(f"🎯 Summary: {success_count}/{len(experiments)} experiments cleaned successfully")
        
    elif args.experiment_dir:
        if not cleanup_experiment(args.experiment_dir, verbose=not args.quiet, regenerate_citations=args.regenerate_citations):
            sys.exit(1)
    else:
        # Interactive mode - find the most recent experiment
        experiments = find_experiments()
        if not experiments:
            print("No experiment directories found.")
            print("Usage: python cleanup_experiment.py [experiment_dir] or --all")
            return
        
        most_recent = experiments[-1]  # Last in sorted list
        print(f"🎯 Most recent experiment: {most_recent}")
        
        response = input("Clean this experiment? [y/N]: ").strip().lower()
        if response in ['y', 'yes']:
            cleanup_experiment(most_recent, verbose=not args.quiet, regenerate_citations=args.regenerate_citations)
        else:
            print("Cleanup cancelled.")

if __name__ == "__main__":
    main() 