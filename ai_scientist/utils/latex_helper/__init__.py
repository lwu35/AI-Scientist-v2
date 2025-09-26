"""
LaTeX Helper Utilities for AI Scientist

This module contains utilities for LaTeX compilation, validation, and optimization:
- LaTeXPackageManager: Automatic package installation and compilation with BibTeX support
- LaTeXTemplateValidator: Template structure validation and fixing
- latex_validation_prompt: LLM prompt generation for LaTeX validation
- setup_latex_conda: Conda environment LaTeX path configuration
"""

from .latex_package_manager import LaTeXPackageManager
from .latex_template_validator import LaTeXTemplateValidator
from .latex_validation_prompt import (
    get_writeup_constraints_prompt,
    validate_writeup_latex,
    get_available_figures,
    get_available_citations
)

__all__ = [
    'LaTeXPackageManager',
    'LaTeXTemplateValidator', 
    'get_writeup_constraints_prompt',
    'validate_writeup_latex',
    'get_available_figures',
    'get_available_citations'
] 