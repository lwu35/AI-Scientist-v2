#!/usr/bin/env python3
"""
Setup script to configure LaTeX properly in conda environment
"""

import os
import subprocess
import sys

def find_latex_installation():
    """Find LaTeX installation on macOS"""
    latex_paths = [
        "/Users/lirenw/Library/TinyTeX/bin/universal-darwin",
        "/usr/local/texlive/2023/bin/universal-darwin",
        "/usr/local/texlive/2024/bin/universal-darwin", 
        "/usr/local/texlive/2025/bin/universal-darwin",
        "/usr/local/bin",
        "/opt/homebrew/bin"
    ]
    
    for path in latex_paths:
        if os.path.exists(path):
            pdflatex = os.path.join(path, 'pdflatex')
            tlmgr = os.path.join(path, 'tlmgr')
            if os.path.exists(pdflatex):
                print(f"✅ Found LaTeX installation: {path}")
                return path
    
    return None

def update_conda_environment():
    """Update conda environment to include LaTeX path"""
    latex_path = find_latex_installation()
    if not latex_path:
        print("❌ No LaTeX installation found")
        return False
    
    # Get conda environment path
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', 'base')
    conda_prefix = os.environ.get('CONDA_PREFIX')
    
    if not conda_prefix:
        print("❌ Not in a conda environment")
        return False
    
    print(f"🔧 Configuring conda environment: {conda_env}")
    print(f"   Environment path: {conda_prefix}")
    
    # Create activation script
    activate_dir = os.path.join(conda_prefix, 'etc', 'conda', 'activate.d')
    deactivate_dir = os.path.join(conda_prefix, 'etc', 'conda', 'deactivate.d')
    
    # Create directories if they don't exist
    os.makedirs(activate_dir, exist_ok=True)
    os.makedirs(deactivate_dir, exist_ok=True)
    
    # Create activation script
    activate_script = os.path.join(activate_dir, 'latex_path.sh')
    with open(activate_script, 'w') as f:
        f.write(f"""#!/bin/bash
# Add LaTeX to PATH when activating conda environment
export LATEX_PATH_BACKUP="$PATH"
export PATH="{latex_path}:$PATH"
echo "🔧 Added LaTeX to PATH: {latex_path}"
""")
    
    # Make it executable
    os.chmod(activate_script, 0o755)
    
    # Create deactivation script
    deactivate_script = os.path.join(deactivate_dir, 'latex_path.sh')
    with open(deactivate_script, 'w') as f:
        f.write("""#!/bin/bash
# Restore original PATH when deactivating conda environment
if [ ! -z "$LATEX_PATH_BACKUP" ]; then
    export PATH="$LATEX_PATH_BACKUP"
    unset LATEX_PATH_BACKUP
fi
""")
    
    # Make it executable
    os.chmod(deactivate_script, 0o755)
    
    print(f"✅ Created activation script: {activate_script}")
    print(f"✅ Created deactivation script: {deactivate_script}")
    
    # Update current session PATH
    current_path = os.environ.get("PATH", "")
    if latex_path not in current_path:
        os.environ["PATH"] = f"{latex_path}:{current_path}"
        print(f"🔧 Updated current session PATH")
    
    return True

def test_latex_access():
    """Test if LaTeX tools are accessible"""
    tools = ['pdflatex', 'tlmgr', 'bibtex']
    success = True
    
    for tool in tools:
        try:
            result = subprocess.run([tool, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ {tool} is accessible")
            else:
                print(f"❌ {tool} failed with return code {result.returncode}")
                success = False
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
            print(f"❌ {tool} not found or not working")
            success = False
    
    return success

def main():
    print("🔧 LaTeX Conda Environment Setup")
    print("=" * 40)
    
    # Check if we're in conda environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if not conda_env:
        print("❌ Not in a conda environment. Please activate your conda environment first:")
        print("   conda activate ai_scientist")
        return 1
    
    print(f"📦 Current conda environment: {conda_env}")
    
    # Find LaTeX installation
    latex_path = find_latex_installation()
    if not latex_path:
        print("\n❌ No LaTeX installation found!")
        print("Please install TinyTeX:")
        print("   1. Install R: https://cran.r-project.org/")
        print("   2. Run in R: install.packages('tinytex'); tinytex::install_tinytex()")
        print("   3. Or install via command line: curl -sL 'https://yihui.org/tinytex/install-bin-unix.sh' | sh")
        return 1
    
    # Update conda environment
    if update_conda_environment():
        print("\n🔄 Testing LaTeX access...")
        if test_latex_access():
            print("\n✅ LaTeX setup complete!")
            print("🔄 Please restart your conda environment to apply changes:")
            print("   conda deactivate")
            print("   conda activate ai_scientist")
            return 0
        else:
            print("\n⚠️  LaTeX setup completed but some tools are not accessible")
            print("You may need to restart your conda environment")
            return 1
    else:
        print("\n❌ Failed to update conda environment")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 