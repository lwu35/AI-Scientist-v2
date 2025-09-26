"""
LaTeX Validation Prompts for LLM-generated writeups
Helps guide LLMs to generate LaTeX that compiles successfully
"""

import os
import re
from typing import List, Dict, Set

def get_available_figures(base_folder: str) -> List[str]:
    """Get list of available figure files in the experiment folder"""
    figures = []
    
    # Check common figure locations
    figure_dirs = [
        os.path.join(base_folder, "figures"),
        os.path.join(base_folder, "plots"), 
        os.path.join(base_folder, "images"),
        base_folder  # Sometimes figures are in the root
    ]
    
    for fig_dir in figure_dirs:
        if os.path.exists(fig_dir):
            for file in os.listdir(fig_dir):
                if file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.eps')):
                    # Store relative path from latex directory
                    if fig_dir.endswith('figures'):
                        figures.append(f"../figures/{file}")
                    else:
                        figures.append(f"../{os.path.basename(fig_dir)}/{file}")
    
    return sorted(figures)

def get_available_citations(base_folder: str) -> Set[str]:
    """Get list of available citations from bibliography files"""
    citations = set()
    
    # Check for bibliography files
    bib_files = []
    for file in os.listdir(base_folder):
        if file.endswith('.bib'):
            bib_files.append(os.path.join(base_folder, file))
    
    # Also check latex directory
    latex_dir = os.path.join(base_folder, "latex")
    if os.path.exists(latex_dir):
        for file in os.listdir(latex_dir):
            if file.endswith('.bib'):
                bib_files.append(os.path.join(latex_dir, file))
    
    # Extract citations from bib files
    for bib_file in bib_files:
        if os.path.exists(bib_file):
            with open(bib_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Find citation keys
                matches = re.findall(r'@[^{]*\{([^,]+),', content)
                citations.update(matches)
    
    return citations

def create_latex_validation_prompt(base_folder: str) -> str:
    """Create a validation prompt to guide LLM LaTeX generation"""
    
    available_figures = get_available_figures(base_folder)
    available_citations = get_available_citations(base_folder)
    
    prompt = f"""
IMPORTANT LATEX GENERATION CONSTRAINTS:

1. AVAILABLE FIGURES ({len(available_figures)} files found):
"""
    
    if available_figures:
        prompt += "   ONLY use these figure files that actually exist:\n"
        for i, fig in enumerate(available_figures[:10], 1):  # Limit to first 10
            prompt += f"   - Figure{i}: {fig}\n"
        if len(available_figures) > 10:
            prompt += f"   - ... and {len(available_figures) - 10} more\n"
        
        prompt += f"""
   Usage: \\includegraphics[width=0.45\\textwidth]{{{available_figures[0]}}}
   
"""
    else:
        prompt += "   ⚠️  NO FIGURE FILES FOUND - DO NOT include any \\includegraphics commands\n\n"
    
    prompt += f"2. AVAILABLE CITATIONS ({len(available_citations)} found):\n"
    
    if available_citations:
        prompt += "   ONLY cite these references that exist in the bibliography:\n"
        citation_list = sorted(list(available_citations))
        for cite in citation_list[:15]:  # Limit to first 15
            prompt += f"   - {cite}\n"
        if len(available_citations) > 15:
            prompt += f"   - ... and {len(available_citations) - 15} more\n"
        
        prompt += f"""
   Usage: \\cite{{{citation_list[0]}}} or \\citep{{{citation_list[0]}}}
   
"""
    else:
        prompt += "   ⚠️  NO CITATIONS FOUND - DO NOT include any \\cite commands\n\n"
    
    prompt += """3. LATEX REQUIREMENTS:
   - Use \\usepackage{iclr2025,times} (NOT iclr2025_icbinb)
   - Graphics path is set to ../figures/ 
   - All figures must be referenced with \\label{fig:name} and \\ref{fig:name}
   - All citations must exist in the bibliography
   - Use standard LaTeX packages only (amsmath, amssymb, graphicx)
   
4. VALIDATION RULES:
   - If a figure doesn't exist, don't reference it
   - If a citation doesn't exist, don't use it  
   - All \\ref{} must have corresponding \\label{}
   - Keep figure numbering sequential (Figure1, Figure2, etc.)

CRITICAL: Only reference files and citations that actually exist. The LaTeX compiler will fail if you reference missing files.
"""
    
    return prompt

def validate_generated_latex(latex_content: str, base_folder: str) -> Dict[str, List[str]]:
    """Validate generated LaTeX content against available resources"""
    issues = {
        'missing_figures': [],
        'missing_citations': [],
        'undefined_refs': [],
        'warnings': []
    }
    
    available_figures = get_available_figures(base_folder)
    available_citations = get_available_citations(base_folder)
    
    # Extract figure references from LaTeX
    figure_refs = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', latex_content)
    for fig_ref in figure_refs:
        if fig_ref not in available_figures:
            issues['missing_figures'].append(fig_ref)
    
    # Extract citation references
    cite_patterns = [r'\\cite\{([^}]+)\}', r'\\citep\{([^}]+)\}', r'\\citet\{([^}]+)\}']
    for pattern in cite_patterns:
        cite_refs = re.findall(pattern, latex_content)
        for cite_ref in cite_refs:
            citations = [c.strip() for c in cite_ref.split(',')]
            for citation in citations:
                if citation not in available_citations:
                    issues['missing_citations'].append(citation)
    
    # Check for undefined references
    label_refs = set(re.findall(r'\\ref\{([^}]+)\}', latex_content))
    label_defs = set(re.findall(r'\\label\{([^}]+)\}', latex_content))
    undefined_refs = label_refs - label_defs
    if undefined_refs:
        issues['undefined_refs'] = list(undefined_refs)
    
    return issues

def create_latex_feedback_prompt(issues: Dict[str, List[str]]) -> str:
    """Create feedback prompt for LLM when validation finds issues"""
    if not any(issues.values()):
        return "✅ LaTeX validation passed - no issues found!"
    
    feedback = "❌ LATEX VALIDATION FAILED - Please fix these issues:\n\n"
    
    if issues['missing_figures']:
        feedback += f"🖼️  MISSING FIGURES ({len(issues['missing_figures'])}):\n"
        for fig in issues['missing_figures'][:5]:
            feedback += f"   - {fig} (file does not exist)\n"
        if len(issues['missing_figures']) > 5:
            feedback += f"   - ... and {len(issues['missing_figures']) - 5} more\n"
        feedback += "   Fix: Remove these \\includegraphics references or use available figures\n\n"
    
    if issues['missing_citations']:
        feedback += f"📚 MISSING CITATIONS ({len(issues['missing_citations'])}):\n"
        for cite in issues['missing_citations'][:5]:
            feedback += f"   - {cite} (not in bibliography)\n"
        if len(issues['missing_citations']) > 5:
            feedback += f"   - ... and {len(issues['missing_citations']) - 5} more\n"
        feedback += "   Fix: Remove these \\cite references or add to bibliography\n\n"
    
    if issues['undefined_refs']:
        feedback += f"🏷️  UNDEFINED REFERENCES ({len(issues['undefined_refs'])}):\n"
        for ref in issues['undefined_refs'][:5]:
            feedback += f"   - \\ref{{{ref}}} (no corresponding \\label{{{ref}}})\n"
        feedback += "   Fix: Add \\label{} commands or remove \\ref{} references\n\n"
    
    feedback += "Please regenerate the LaTeX with these issues fixed."
    
    return feedback

# Example usage functions
def get_writeup_constraints_prompt(base_folder: str) -> str:
    """Get constraints prompt for writeup generation"""
    return create_latex_validation_prompt(base_folder)

def validate_writeup_latex(latex_content: str, base_folder: str) -> str:
    """Validate writeup LaTeX and return feedback"""
    issues = validate_generated_latex(latex_content, base_folder)
    return create_latex_feedback_prompt(issues) 