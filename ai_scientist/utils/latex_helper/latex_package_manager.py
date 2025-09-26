#!/usr/bin/env python3
"""
LaTeX Package Manager for AI Scientist
Automatically detects and installs missing LaTeX packages during compilation
"""

import os
import re
import subprocess
import sys
from typing import List, Set, Optional, Tuple, Dict
import logging
import shutil # Added for backup

# Import template validator
try:
    from .latex_template_validator import LaTeXTemplateValidator
    TEMPLATE_VALIDATOR_AVAILABLE = True
except ImportError:
    TEMPLATE_VALIDATOR_AVAILABLE = False

logger = logging.getLogger(__name__)

class LaTeXPackageManager:
    """Manages LaTeX package installation and compilation with validation"""
    
    # Common packages needed for scientific papers
    ESSENTIAL_PACKAGES = {
        'siunitx', 'multirow', 'algorithm2e', 'algorithms', 'algorithmicx',
        'amsmath', 'amsfonts', 'amssymb', 'amsthm', 'mathtools',
        'graphicx', 'subfigure', 'subcaption', 'booktabs', 'array',
        'longtable', 'tabularx', 'rotating', 'pdflscape',
        'hyperref', 'url', 'natbib', 'biblatex', 'cite',
        'xcolor', 'tikz', 'pgfplots', 'listings', 'verbatim',
        'geometry', 'fancyhdr', 'setspace', 'enumitem',
        'caption', 'float', 'placeins', 'afterpage'
    }
    
    # Package name mappings (LaTeX name -> TinyTeX package name)
    PACKAGE_MAPPINGS = {
        'algorithmic': 'algorithms',
        'algorithm': 'algorithms',
        'subcaption': 'caption',
        'pdflscape': 'pdflscape',
        'biblatex': 'biblatex',
        'pgfplots': 'pgf',
        'tikz': 'pgf',
    }
    
    def __init__(self):
        self.installed_packages: Set[str] = set()
        self.failed_packages: Set[str] = set()
        self.logger = logging.getLogger(__name__)

    def check_latex_installation(self) -> bool:
        """Check if LaTeX is properly installed"""
        # Common LaTeX installation paths
        latex_paths = [
            "/Users/lirenw/Library/TinyTeX/bin/universal-darwin",
            "/usr/local/texlive/2023/bin/universal-darwin",
            "/usr/local/texlive/2024/bin/universal-darwin", 
            "/usr/local/texlive/2025/bin/universal-darwin",
            "/usr/local/bin",
            "/opt/homebrew/bin"
        ]
        
        # First try with current PATH
        try:
            result = subprocess.run(['pdflatex', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ pdflatex found: {result.stdout.split()[0]} {result.stdout.split()[1]}")
                return True
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try with extended PATH
        for latex_path in latex_paths:
            if os.path.exists(latex_path):
                pdflatex_path = os.path.join(latex_path, 'pdflatex')
                if os.path.exists(pdflatex_path):
                    try:
                        result = subprocess.run([pdflatex_path, '--version'], 
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            print(f"✅ pdflatex found at: {pdflatex_path}")
                            # Update PATH for this session
                            current_path = os.environ.get("PATH", "")
                            if latex_path not in current_path:
                                os.environ["PATH"] = f"{latex_path}:{current_path}"
                                print(f"🔧 Added {latex_path} to PATH")
                            return True
                    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
                        continue
        
        print("❌ pdflatex not found or not working")
        return False
    
    def check_tlmgr_installation(self) -> bool:
        """Check if tlmgr (TinyTeX package manager) is available"""
        # Common LaTeX installation paths
        latex_paths = [
            "/Users/lirenw/Library/TinyTeX/bin/universal-darwin",
            "/usr/local/texlive/2023/bin/universal-darwin",
            "/usr/local/texlive/2024/bin/universal-darwin", 
            "/usr/local/texlive/2025/bin/universal-darwin",
            "/usr/local/bin",
            "/opt/homebrew/bin"
        ]
        
        # First try with current PATH
        try:
            result = subprocess.run(['tlmgr', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ tlmgr found")
                return True
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try with extended PATH
        for latex_path in latex_paths:
            if os.path.exists(latex_path):
                tlmgr_path = os.path.join(latex_path, 'tlmgr')
                if os.path.exists(tlmgr_path):
                    try:
                        result = subprocess.run([tlmgr_path, '--version'], 
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            print(f"✅ tlmgr found at: {tlmgr_path}")
                            # Update PATH for this session
                            current_path = os.environ.get("PATH", "")
                            if latex_path not in current_path:
                                os.environ["PATH"] = f"{latex_path}:{current_path}"
                                print(f"🔧 Added {latex_path} to PATH")
                            return True
                    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
                        continue
        
        print("❌ tlmgr not found - automatic package installation unavailable")
        return False
    
    def install_essential_packages(self) -> bool:
        """Install essential packages for scientific papers"""
        if not self.check_tlmgr_installation():
            return False
        
        print("📦 Installing essential LaTeX packages...")
        success_count = 0
        
        for package in self.ESSENTIAL_PACKAGES:
            if self.install_package(package, quiet=True):
                success_count += 1
        
        print(f"✅ Successfully installed {success_count}/{len(self.ESSENTIAL_PACKAGES)} essential packages")
        return success_count > len(self.ESSENTIAL_PACKAGES) * 0.8  # 80% success rate
    
    def install_package(self, package_name: str, quiet: bool = False) -> bool:
        """Install a specific LaTeX package"""
        if package_name in self.installed_packages:
            return True
        
        if package_name in self.failed_packages:
            return False
        
        # Map package name if needed
        tlmgr_package = self.PACKAGE_MAPPINGS.get(package_name, package_name)
        
        try:
            if not quiet:
                print(f"📦 Installing LaTeX package: {package_name}")
            
            result = subprocess.run(
                ['tlmgr', 'install', tlmgr_package],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0:
                self.installed_packages.add(package_name)
                if not quiet:
                    print(f"✅ Successfully installed: {package_name}")
                return True
            else:
                self.failed_packages.add(package_name)
                if not quiet:
                    print(f"❌ Failed to install {package_name}: {result.stderr.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout installing {package_name}")
            self.failed_packages.add(package_name)
            return False
        except Exception as e:
            if not quiet:
                print(f"❌ Error installing {package_name}: {e}")
            self.failed_packages.add(package_name)
            return False
    
    def extract_missing_packages_from_log(self, log_content: str) -> List[str]:
        """Extract missing package names from LaTeX compilation log"""
        missing_packages = []
        
        # Pattern 1: ! LaTeX Error: File `package.sty' not found.
        pattern1 = re.compile(r"! LaTeX Error: File `([^'`]+)\.sty' not found", re.IGNORECASE)
        matches1 = pattern1.findall(log_content)
        missing_packages.extend(matches1)
        
        # Pattern 2: ! I can't find file `package.sty'.
        pattern2 = re.compile(r"! I can't find file `([^'`]+)\.sty'", re.IGNORECASE)
        matches2 = pattern2.findall(log_content)
        missing_packages.extend(matches2)
        
        # Pattern 3: LaTeX Error: File `package.cls' not found.
        pattern3 = re.compile(r"! LaTeX Error: File `([^'`]+)\.cls' not found", re.IGNORECASE)
        matches3 = pattern3.findall(log_content)
        missing_packages.extend(matches3)
        
        # Pattern 4: File `package' not found
        pattern4 = re.compile(r"File `([^'`]+)' not found", re.IGNORECASE)
        matches4 = pattern4.findall(log_content)
        # Filter to only .sty and .cls files
        matches4 = [m for m in matches4 if m.endswith('.sty') or m.endswith('.cls')]
        missing_packages.extend([m.replace('.sty', '').replace('.cls', '') for m in matches4])
        
        # Pattern 5: Emergency stop after missing file
        if "Emergency stop" in log_content:
            # Look for the last file that couldn't be found
            emergency_pattern = re.compile(r"l\.\d+\s+\\usepackage\s*\{([^}]+)\}", re.IGNORECASE)
            emergency_matches = emergency_pattern.findall(log_content)
            missing_packages.extend(emergency_matches)
        
        # Remove duplicates and return
        unique_packages = list(set(missing_packages))
        print(f"🔍 Extracted missing packages: {unique_packages}")
        return unique_packages
    
    def compile_latex_with_auto_install(self, tex_file: str, max_attempts: int = 3) -> Tuple[bool, str]:
        """
        Compile LaTeX file with automatic package installation
        
        Returns:
            (success: bool, log_content: str)
        """
        if not os.path.exists(tex_file):
            return False, f"LaTeX file not found: {tex_file}"
        
        print(f"🔧 Compiling LaTeX file: {tex_file}")
        working_dir = os.path.dirname(os.path.abspath(tex_file))
        
        for attempt in range(max_attempts):
            print(f"📝 Compilation attempt {attempt + 1}/{max_attempts}")
            
            # Run pdflatex
            try:
                result = subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', os.path.basename(tex_file)],
                    cwd=working_dir,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                log_content = result.stdout + result.stderr
                
                if result.returncode == 0:
                    # Check if we need to run BibTeX (look for citations and bibliography)
                    tex_basename = os.path.basename(tex_file).replace('.tex', '')
                    aux_file = os.path.join(working_dir, f"{tex_basename}.aux")
                    
                    # Check if there are citations that need BibTeX processing
                    needs_bibtex = False
                    if os.path.exists(aux_file):
                        with open(aux_file, 'r', encoding='utf-8', errors='ignore') as f:
                            aux_content = f.read()
                        needs_bibtex = ('\\citation{' in aux_content or 
                                      '\\bibdata{' in aux_content or 
                                      'There were undefined citations' in log_content)
                    
                    if needs_bibtex:
                        print("📚 Citations detected, running BibTeX...")
                        try:
                            bibtex_result = subprocess.run(
                                ['bibtex', tex_basename],
                                cwd=working_dir,
                                capture_output=True,
                                text=True,
                                timeout=60
                            )
                            
                            if bibtex_result.returncode == 0:
                                print("✅ BibTeX processing successful!")
                                
                                # Run pdflatex again to incorporate bibliography
                                print("📝 Running pdflatex again to incorporate bibliography...")
                                for bibtex_pass in range(2):  # Usually need 2 more passes
                                    result2 = subprocess.run(
                                        ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', os.path.basename(tex_file)],
                                        cwd=working_dir,
                                        capture_output=True,
                                        text=True,
                                        timeout=120
                                    )
                                    if result2.returncode != 0:
                                        print(f"⚠️  pdflatex pass {bibtex_pass + 2} failed, but continuing...")
                                        break
                                    print(f"✅ pdflatex pass {bibtex_pass + 2} successful!")
                                
                                # Update log content with final compilation
                                log_content = result2.stdout + result2.stderr if 'result2' in locals() else log_content
                            else:
                                print(f"⚠️  BibTeX processing failed: {bibtex_result.stderr}")
                                print("   Continuing with pdflatex-only compilation...")
                                
                        except Exception as e:
                            print(f"⚠️  BibTeX error: {e}")
                            print("   Continuing with pdflatex-only compilation...")
                    
                    pdf_file = tex_file.replace('.tex', '.pdf')
                    if os.path.exists(pdf_file):
                        print(f"✅ LaTeX compilation successful!")
                        return True, log_content
                
                # Extract missing packages from log
                missing_packages = self.extract_missing_packages_from_log(log_content)
                
                if not missing_packages:
                    print(f"❌ LaTeX compilation failed (no missing packages detected)")
                    print(f"Return code: {result.returncode}")
                    print(f"Full stdout: {result.stdout[-1000:]}")  # Last 1000 chars
                    print(f"Full stderr: {result.stderr[-1000:]}")   # Last 1000 chars
                    
                    # Look for other common LaTeX errors
                    common_errors = [
                        "Undefined control sequence",
                        "Missing $ inserted", 
                        "Extra alignment tab",
                        "Illegal parameter number",
                        "File ended while scanning",
                        "Emergency stop",
                        "Fatal error occurred"
                    ]
                    
                    for error in common_errors:
                        if error in log_content:
                            print(f"🔍 Detected LaTeX error: {error}")
                            break
                    
                    return False, log_content
                
                print(f"📦 Missing packages detected: {missing_packages}")
                
                # Install missing packages
                installed_any = False
                for package in missing_packages:
                    if self.install_package(package):
                        installed_any = True
                    else:
                        # Special handling for common package name variations
                        if package == "iclr2025_icbinb" and os.path.exists(os.path.join(working_dir, "iclr2025.sty")):
                            print(f"🔧 Creating symlink: iclr2025_icbinb.sty -> iclr2025.sty")
                            try:
                                symlink_path = os.path.join(working_dir, "iclr2025_icbinb.sty")
                                if not os.path.exists(symlink_path):
                                    os.symlink("iclr2025.sty", symlink_path)
                                    installed_any = True
                                    print(f"✅ Created symlink for {package}")
                            except Exception as e:
                                print(f"❌ Failed to create symlink: {e}")
                
                if not installed_any:
                    print(f"❌ Could not install any missing packages")
                    return False, log_content
                
            except subprocess.TimeoutExpired:
                print(f"⏰ LaTeX compilation timeout (attempt {attempt + 1})")
                if attempt == max_attempts - 1:
                    return False, "Compilation timeout"
            except Exception as e:
                print(f"❌ LaTeX compilation error: {e}")
                return False, str(e)
        
        return False, "Max compilation attempts exceeded"

    def validate_latex_file(self, tex_file: str) -> Dict[str, List[str]]:
        """Validate LaTeX file for missing references and files"""
        issues = {
            'missing_figures': [],
            'missing_style_files': [],
            'undefined_labels': [],
            'undefined_citations': [],
            'warnings': []
        }
        
        if not os.path.exists(tex_file):
            issues['warnings'].append(f"LaTeX file not found: {tex_file}")
            return issues
        
        working_dir = os.path.dirname(tex_file)
        
        with open(tex_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Check for missing figure files
        figure_patterns = [
            r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',
            r'\\includegraphics\*(?:\[[^\]]*\])?\{([^}]+)\}',
        ]
        
        for pattern in figure_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # Handle relative paths and extensions
                figure_file = match.strip()
                if not figure_file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.eps')):
                    figure_file += '.pdf'  # Default extension
                
                # Check in working directory and figures subdirectory
                possible_paths = [
                    os.path.join(working_dir, figure_file),
                    os.path.join(working_dir, '..', 'figures', os.path.basename(figure_file)),
                    os.path.join(working_dir, 'figures', os.path.basename(figure_file)),
                ]
                
                if not any(os.path.exists(path) for path in possible_paths):
                    issues['missing_figures'].append(figure_file)
        
        # Check for missing style/class files
        package_patterns = [
            r'\\usepackage(?:\[[^\]]*\])?\{([^}]+)\}',
            r'\\documentclass(?:\[[^\]]*\])?\{([^}]+)\}',
        ]
        
        for pattern in package_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                packages = [pkg.strip() for pkg in match.split(',')]
                for package in packages:
                    if package in ['times', 'amsmath', 'amssymb', 'graphicx']:
                        continue  # Skip standard packages
                    
                    style_file = f"{package}.sty"
                    class_file = f"{package}.cls"
                    
                    style_path = os.path.join(working_dir, style_file)
                    class_path = os.path.join(working_dir, class_file)
                    
                    if not os.path.exists(style_path) and not os.path.exists(class_path):
                        # Check if it's a standard LaTeX package (rough heuristic)
                        if not self._is_standard_package(package):
                            issues['missing_style_files'].append(package)
        
        # Check for undefined labels (referenced but not defined)
        label_refs = set(re.findall(r'\\ref\{([^}]+)\}', content))
        label_refs.update(re.findall(r'\\eqref\{([^}]+)\}', content))
        label_refs.update(re.findall(r'\\pageref\{([^}]+)\}', content))
        
        label_defs = set(re.findall(r'\\label\{([^}]+)\}', content))
        
        undefined_labels = label_refs - label_defs
        if undefined_labels:
            issues['undefined_labels'] = list(undefined_labels)
        
        # Check for undefined citations
        cite_refs = set()
        cite_patterns = [
            r'\\cite\{([^}]+)\}',
            r'\\citep\{([^}]+)\}',
            r'\\citet\{([^}]+)\}',
            r'\\citealp\{([^}]+)\}',
            r'\\citealt\{([^}]+)\}',
        ]
        
        for pattern in cite_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                citations = [cite.strip() for cite in match.split(',')]
                cite_refs.update(citations)
        
        # Check if bibliography file exists and extract available citations
        bib_files = re.findall(r'\\bibliography\{([^}]+)\}', content)
        cite_defs = set()
        
        # Check bibliography files referenced in \bibliography{}
        for bib_file in bib_files:
            bib_path = os.path.join(working_dir, f"{bib_file}.bib")
            if os.path.exists(bib_path):
                with open(bib_path, 'r', encoding='utf-8', errors='ignore') as bf:
                    bib_content = bf.read()
                    cite_defs.update(re.findall(r'@[^{]*\{([^,]+),', bib_content))
        
        # Check for any .bib files in the directory (even if not explicitly referenced)
        if not cite_defs:
            for file in os.listdir(working_dir):
                if file.endswith('.bib'):
                    bib_path = os.path.join(working_dir, file)
                    try:
                        with open(bib_path, 'r', encoding='utf-8', errors='ignore') as bf:
                            bib_content = bf.read()
                            cite_defs.update(re.findall(r'@[^{]*\{([^,]+),', bib_content))
                    except:
                        continue
        
        # Also check parent directory for .bib files (common in experiments)
        if not cite_defs:
            parent_dir = os.path.dirname(working_dir)
            if os.path.exists(parent_dir):
                for file in os.listdir(parent_dir):
                    if file.endswith('.bib'):
                        bib_path = os.path.join(parent_dir, file)
                        try:
                            with open(bib_path, 'r', encoding='utf-8', errors='ignore') as bf:
                                bib_content = bf.read()
                                cite_defs.update(re.findall(r'@[^{]*\{([^,]+),', bib_content))
                        except:
                            continue
        
        # Also check for inline bibliography (filecontents)
        filecontents_match = re.search(r'\\begin\{filecontents\}\{[^}]*\.bib\}(.*?)\\end\{filecontents\}', content, re.DOTALL)
        if filecontents_match:
            bib_content = filecontents_match.group(1)
            cite_defs.update(re.findall(r'@[^{]*\{([^,]+),', bib_content))
        
        # Only report as undefined if we actually found bibliography files but the citations aren't in them
        if cite_defs:  # We found some bibliography content
            undefined_citations = cite_refs - cite_defs
            if undefined_citations:
                issues['undefined_citations'] = list(undefined_citations)
        else:
            # No bibliography found at all - this is a different issue
            if cite_refs:
                issues['warnings'].append(f"Citations found but no bibliography files detected: {list(cite_refs)}")
                # Don't mark as undefined_citations since there's no bibliography to check against
        
        return issues

    def _is_standard_package(self, package_name: str) -> bool:
        """Check if a package is likely a standard LaTeX package"""
        standard_packages = {
            'amsmath', 'amssymb', 'amsfonts', 'graphicx', 'xcolor', 'color',
            'booktabs', 'array', 'multirow', 'natbib', 'hyperref', 'geometry',
            'fancyhdr', 'titlesec', 'caption', 'subcaption', 'float', 'placeins',
            'afterpage', 'times', 'helvet', 'courier', 'palatino', 'mathpazo',
            'txfonts', 'pxfonts', 'lmodern', 'fourier', 'kpfonts', 'libertine'
        }
        return package_name.lower() in standard_packages

    def fix_latex_issues(self, tex_file: str, issues: Dict[str, List[str]]) -> bool:
        """Attempt to fix common LaTeX issues"""
        if not os.path.exists(tex_file):
            return False
        
        working_dir = os.path.dirname(tex_file)
        fixed_anything = False
        
        with open(tex_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original_content = content
        
        # Fix missing figures by commenting them out or using draft mode
        if issues['missing_figures']:
            print(f"🔧 Fixing {len(issues['missing_figures'])} missing figure references...")
            for figure in issues['missing_figures']:
                # Replace includegraphics with a placeholder
                patterns = [
                    rf'\\includegraphics(?:\[[^\]]*\])?\{{{re.escape(figure)}\}}',
                    rf'\\includegraphics\*(?:\[[^\]]*\])?\{{{re.escape(figure)}\}}',
                ]
                
                for pattern in patterns:
                    if re.search(pattern, content):
                        # Use raw string and escape properly for re.sub
                        placeholder = r"\\fbox{\\parbox{0.45\\textwidth}{\\centering Missing Figure: " + os.path.basename(figure) + r"}}"
                        content = re.sub(pattern, placeholder, content)
                        fixed_anything = True
                        print(f"  ✅ Replaced missing figure: {figure}")
        
        # Fix undefined labels by commenting out references
        if issues['undefined_labels']:
            print(f"🔧 Fixing {len(issues['undefined_labels'])} undefined label references...")
            for label in issues['undefined_labels']:
                patterns = [
                    rf'\\ref\{{{re.escape(label)}\}}',
                    rf'\\eqref\{{{re.escape(label)}\}}',
                    rf'\\pageref\{{{re.escape(label)}\}}',
                ]
                
                for pattern in patterns:
                    if re.search(pattern, content):
                        content = re.sub(pattern, f"[REF:{label}]", content)
                        fixed_anything = True
                        print(f"  ✅ Replaced undefined reference: {label}")
        
        # Handle undefined citations more conservatively
        if issues['undefined_citations']:
            print(f"⚠️  Found {len(issues['undefined_citations'])} undefined citations - checking if they should be preserved...")
            
            # Only fix citations if there are NO bibliography files at all
            bib_files_exist = False
            working_dir = os.path.dirname(tex_file)
            
            # Check for bibliography files in current and parent directories
            for check_dir in [working_dir, os.path.dirname(working_dir)]:
                if os.path.exists(check_dir):
                    for file in os.listdir(check_dir):
                        if file.endswith('.bib'):
                            bib_files_exist = True
                            break
                if bib_files_exist:
                    break
            
            # Also check for inline bibliography (filecontents)
            if not bib_files_exist and 'filecontents' in content and '.bib' in content:
                bib_files_exist = True
            
            if not bib_files_exist:
                print("🔧 No bibliography files found - replacing undefined citations with plain text...")
                for citation in issues['undefined_citations']:
                    cite_patterns = [
                        rf'\\cite\{{{re.escape(citation)}\}}',
                        rf'\\citep\{{{re.escape(citation)}\}}',
                        rf'\\citet\{{{re.escape(citation)}\}}',
                    ]
                    
                    for pattern in cite_patterns:
                        if re.search(pattern, content):
                            content = re.sub(pattern, f"[{citation}]", content)
                            fixed_anything = True
                            print(f"  ✅ Replaced undefined citation: {citation}")
            else:
                print("✅ Bibliography files found - preserving citation commands for BibTeX processing")
                print("   Citations will be resolved during compilation with bibliography")
        
        # Save the fixed content
        if fixed_anything:
            backup_file = tex_file + '.backup'
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(original_content)
            print(f"📄 Created backup: {backup_file}")
            
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed LaTeX file: {tex_file}")
        
        return fixed_anything

    def validate_and_fix_bibtex_files(self, tex_file_dir: str, auto_fix: bool = True) -> Tuple[bool, List[str]]:
        """
        Validate and fix BibTeX bibliography files for common syntax errors
        
        Args:
            tex_file_dir: Directory containing LaTeX and bibliography files
            auto_fix: Whether to automatically fix detected issues
            
        Returns:
            (success: bool, issues_found: List[str])
        """
        issues_found = []
        success = True
        
        # Check for .bbl files (processed bibliography)
        bbl_files = [f for f in os.listdir(tex_file_dir) if f.endswith('.bbl')]
        
        for bbl_file in bbl_files:
            bbl_path = os.path.join(tex_file_dir, bbl_file)
            print(f"🔍 Validating BibTeX file: {bbl_file}")
            
            try:
                with open(bbl_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Fix 1: Unescaped ampersands in journal names and titles
                # Look for patterns like "Journal & Management" and replace with "Journal \& Management"
                ampersand_pattern = r'([^\\])&([^&])'  # & not preceded by \ and not followed by &
                if re.search(ampersand_pattern, content):
                    issues_found.append(f"Unescaped ampersands found in {bbl_file}")
                    if auto_fix:
                        content = re.sub(ampersand_pattern, r'\1\\&\2', content)
                        print(f"🔧 Fixed unescaped ampersands in {bbl_file}")
                
                # Fix 2: Unescaped underscores in URLs or titles
                underscore_pattern = r'([^\\])_([^{])'  # _ not preceded by \ and not in {}
                if re.search(underscore_pattern, content):
                    issues_found.append(f"Unescaped underscores found in {bbl_file}")
                    if auto_fix:
                        content = re.sub(underscore_pattern, r'\1\\_\2', content)
                        print(f"🔧 Fixed unescaped underscores in {bbl_file}")
                
                # Fix 3: Unescaped hash symbols
                hash_pattern = r'([^\\])#([^{])'  # # not preceded by \ and not in {}
                if re.search(hash_pattern, content):
                    issues_found.append(f"Unescaped hash symbols found in {bbl_file}")
                    if auto_fix:
                        content = re.sub(hash_pattern, r'\1\\#\2', content)
                        print(f"🔧 Fixed unescaped hash symbols in {bbl_file}")
                
                # Fix 4: Unescaped percent symbols
                percent_pattern = r'([^\\])%([^{])'  # % not preceded by \ and not in {}
                if re.search(percent_pattern, content):
                    issues_found.append(f"Unescaped percent symbols found in {bbl_file}")
                    if auto_fix:
                        content = re.sub(percent_pattern, r'\1\\%\2', content)
                        print(f"🔧 Fixed unescaped percent symbols in {bbl_file}")
                
                # Save the fixed content if changes were made
                if auto_fix and content != original_content:
                    # Create backup
                    backup_path = bbl_path + '.syntax_backup'
                    shutil.copy2(bbl_path, backup_path)
                    
                    with open(bbl_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"💾 Fixed BibTeX file saved, backup at: {backup_path}")
                
            except Exception as e:
                issues_found.append(f"Error processing {bbl_file}: {e}")
                success = False
                print(f"❌ Error validating {bbl_file}: {e}")
        
        # Also check .bib files (source bibliography)
        bib_files = [f for f in os.listdir(tex_file_dir) if f.endswith('.bib')]
        
        for bib_file in bib_files:
            bib_path = os.path.join(tex_file_dir, bib_file)
            print(f"🔍 Validating source bibliography: {bib_file}")
            
            try:
                with open(bib_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Fix unescaped ampersands in .bib files (more comprehensive)
                # Pattern 1: & in journal names, titles, etc.
                field_ampersand_pattern = r'(\s*=\s*\{[^}]*[^\\])&([^}]*\})'
                if re.search(field_ampersand_pattern, content):
                    issues_found.append(f"Unescaped ampersands in fields found in {bib_file}")
                    if auto_fix:
                        content = re.sub(field_ampersand_pattern, r'\1\\&\2', content)
                        print(f"🔧 Fixed unescaped ampersands in bibliography fields in {bib_file}")
                
                # Fix HTML entities that shouldn't be in BibTeX
                html_entities = {
                    '&amp;': '\\&',
                    '&lt;': '<',
                    '&gt;': '>',
                    '&quot;': '"',
                    '&#39;': "'"
                }
                
                for entity, replacement in html_entities.items():
                    if entity in content:
                        issues_found.append(f"HTML entity {entity} found in {bib_file}")
                        if auto_fix:
                            content = content.replace(entity, replacement)
                            print(f"🔧 Fixed HTML entity {entity} → {replacement} in {bib_file}")
                
                # Fix unescaped special characters in other contexts
                # Pattern 2: & in author names, addresses, etc.
                general_ampersand_pattern = r'([^\\]&)([^&\s])'
                if re.search(general_ampersand_pattern, content):
                    issues_found.append(f"Unescaped ampersands in general content found in {bib_file}")
                    if auto_fix:
                        content = re.sub(general_ampersand_pattern, r'\1\\&\2', content)
                        print(f"🔧 Fixed unescaped ampersands in general content in {bib_file}")
                
                # Save the fixed content if changes were made
                if auto_fix and content != original_content:
                    # Create backup
                    backup_path = bib_path + '.syntax_backup'
                    shutil.copy2(bib_path, backup_path)
                    
                    with open(bib_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"💾 Fixed source bibliography saved, backup at: {backup_path}")
                
            except Exception as e:
                issues_found.append(f"Error processing {bib_file}: {e}")
                success = False
                print(f"❌ Error validating {bib_file}: {e}")
        
        return success, issues_found
    
    def detect_bibtex_compilation_errors(self, log_content: str) -> List[str]:
        """
        Detect BibTeX-related compilation errors from LaTeX log
        
        Args:
            log_content: LaTeX compilation log content
            
        Returns:
            List of detected BibTeX error messages
        """
        bibtex_errors = []
        
        # Error patterns to look for
        error_patterns = [
            (r'! Misplaced alignment tab character &', 'Unescaped ampersand in bibliography'),
            (r'! Undefined control sequence.*\\&', 'Malformed ampersand escape'),
            (r'! LaTeX Error: Something\'s wrong--perhaps a missing \\item', 'Bibliography formatting error'),
            (r'Package natbib Warning: Citation .* undefined', 'Undefined citations'),
            (r'! Package natbib Error:', 'NatBib package error'),
            (r'! I can\'t find file.*\.bbl', 'Missing bibliography file'),
        ]
        
        for pattern, description in error_patterns:
            if re.search(pattern, log_content, re.IGNORECASE):
                bibtex_errors.append(description)
        
        return bibtex_errors

    def compile_latex_with_validation(self, tex_file: str, max_attempts: int = 3, auto_fix: bool = True) -> Tuple[bool, str]:
        """Compile LaTeX with pre-compilation validation and fixing"""
        print(f"🔍 Validating LaTeX file: {tex_file}")
        
        # Step 0: Template structure validation (new!)
        if TEMPLATE_VALIDATOR_AVAILABLE and auto_fix:
            print("🏗️  Performing template structure validation...")
            try:
                validator = LaTeXTemplateValidator()
                results = validator.validate_and_fix_template(tex_file, auto_fix=True)
                
                if results["success"]:
                    if results["needs_fixing"]:
                        print(f"🔧 Fixed {len(results['fixes_applied'])} template structure issues:")
                        for fix in results['fixes_applied'][:3]:  # Show first 3
                            print(f"   • {fix}")
                        if len(results['fixes_applied']) > 3:
                            print(f"   • ... and {len(results['fixes_applied']) - 3} more")
                    else:
                        print("✅ Template structure validation passed")
                else:
                    print(f"⚠️  Template structure validation failed: {results.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"⚠️  Template structure validation failed: {e}")
                print("   Proceeding with content validation")
        elif not TEMPLATE_VALIDATOR_AVAILABLE:
            print("ℹ️  Template structure validator not available")
        
        # Step 1: Validate the file content
        issues = self.validate_latex_file(tex_file)
        
        # Report issues
        total_issues = sum(len(issue_list) for issue_list in issues.values() if isinstance(issue_list, list))
        
        if total_issues > 0:
            print(f"⚠️  Found {total_issues} potential issues:")
            
            if issues['missing_figures']:
                print(f"  📷 Missing figures ({len(issues['missing_figures'])}): {', '.join(issues['missing_figures'][:5])}")
                if len(issues['missing_figures']) > 5:
                    print(f"    ... and {len(issues['missing_figures']) - 5} more")
            
            if issues['missing_style_files']:
                print(f"  📄 Missing style files ({len(issues['missing_style_files'])}): {', '.join(issues['missing_style_files'])}")
            
            if issues['undefined_labels']:
                print(f"  🏷️  Undefined labels ({len(issues['undefined_labels'])}): {', '.join(issues['undefined_labels'][:3])}")
                if len(issues['undefined_labels']) > 3:
                    print(f"    ... and {len(issues['undefined_labels']) - 3} more")
            
            if issues['undefined_citations']:
                print(f"  📚 Undefined citations ({len(issues['undefined_citations'])}): {', '.join(issues['undefined_citations'][:3])}")
                if len(issues['undefined_citations']) > 3:
                    print(f"    ... and {len(issues['undefined_citations']) - 3} more")
            
            # Step 2: Try to fix issues automatically
            if auto_fix:
                print("🔧 Attempting to fix issues automatically...")
                if self.fix_latex_issues(tex_file, issues):
                    print("✅ Issues fixed, proceeding with compilation")
                else:
                    print("⚠️  Could not fix all issues, attempting compilation anyway")
            else:
                print("⚠️  Auto-fix disabled, attempting compilation with issues")
        else:
            print("✅ No issues found, proceeding with compilation")
        
        # Step 2.5: BibTeX validation and fixing (new!)
        tex_file_dir = os.path.dirname(os.path.abspath(tex_file))
        if auto_fix:
            print("📚 Performing BibTeX validation...")
            try:
                bibtex_success, bibtex_issues = self.validate_and_fix_bibtex_files(tex_file_dir, auto_fix=True)
                
                if bibtex_issues:
                    print(f"🔧 Fixed {len(bibtex_issues)} BibTeX issues:")
                    for issue in bibtex_issues[:3]:  # Show first 3
                        print(f"   • {issue}")
                    if len(bibtex_issues) > 3:
                        print(f"   • ... and {len(bibtex_issues) - 3} more")
                else:
                    print("✅ No BibTeX issues found")
                    
            except Exception as e:
                print(f"⚠️  BibTeX validation failed: {e}")
                print("   Proceeding with compilation")
        
        # Step 3: Compile with the existing method
        success, log_content = self.compile_latex_with_auto_install(tex_file, max_attempts)
        
        # Step 4: Post-compilation BibTeX error detection
        if not success and log_content:
            bibtex_errors = self.detect_bibtex_compilation_errors(log_content)
            if bibtex_errors:
                print("📚 Detected BibTeX-related compilation errors:")
                for error in bibtex_errors:
                    print(f"   • {error}")
                
                # If we found BibTeX errors and auto_fix is enabled, try to fix and recompile
                if auto_fix:
                    print("🔧 Attempting to fix BibTeX errors and recompile...")
                    bibtex_success, bibtex_issues = self.validate_and_fix_bibtex_files(tex_file_dir, auto_fix=True)
                    if bibtex_issues:
                        print("🔄 Retrying compilation after BibTeX fixes...")
                        success, log_content = self.compile_latex_with_auto_install(tex_file, 1)  # Single retry
        
        return success, log_content
    
    def create_package_install_script(self, output_file: str = "install_latex_packages.sh"):
        """Create a shell script to install all essential packages"""
        script_content = """#!/bin/bash
# LaTeX Package Installation Script for AI Scientist
# Run this script to install essential packages for scientific paper generation

echo "🚀 Installing essential LaTeX packages for AI Scientist..."

# Check if tlmgr is available
if ! command -v tlmgr &> /dev/null; then
    echo "❌ tlmgr not found. Please install TinyTeX first:"
    echo "   R: tinytex::install_tinytex()"
    echo "   Or visit: https://yihui.org/tinytex/"
    exit 1
fi

# Essential packages for scientific papers
PACKAGES=(
    "siunitx" "multirow" "algorithm2e" "algorithms"
    "amsmath" "amsfonts" "amssymb" "amsthm" "mathtools"
    "graphicx" "subfigure" "booktabs" "array"
    "hyperref" "url" "natbib" "cite"
    "xcolor" "tikz" "pgfplots" "listings"
    "geometry" "fancyhdr" "setspace" "enumitem"
    "caption" "float" "placeins"
)

success_count=0
total_count=${#PACKAGES[@]}

for package in "${PACKAGES[@]}"; do
    echo "📦 Installing $package..."
    if tlmgr install "$package" 2>/dev/null; then
        echo "✅ $package installed successfully"
        ((success_count++))
    else
        echo "⚠️  $package installation failed (may already be installed)"
    fi
done

echo "🎉 Installation complete: $success_count/$total_count packages processed"
echo "✅ LaTeX environment ready for AI Scientist!"
"""
        
        with open(output_file, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(output_file, 0o755)
        print(f"📝 Created package installation script: {output_file}")
        print(f"   Run with: ./{output_file}")


def main():
    """Main function for testing the package manager"""
    manager = LaTeXPackageManager()
    
    print("🔍 LaTeX Environment Check")
    print("-" * 40)
    
    latex_ok = manager.check_latex_installation()
    tlmgr_ok = manager.check_tlmgr_installation()
    
    if not latex_ok:
        print("\n❌ LaTeX not properly installed. Please install TinyTeX or TeXLive.")
        sys.exit(1)
    
    if tlmgr_ok:
        print("\n📦 Installing essential packages...")
        manager.install_essential_packages()
    
    # Create installation script
    manager.create_package_install_script()
    
    print("\n✅ LaTeX package manager setup complete!")


if __name__ == "__main__":
    main() 