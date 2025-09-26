#!/usr/bin/env python3
"""
LaTeX Template Structure Validator
Validates and fixes common LaTeX document structure issues that cause compilation failures.
"""

import os
import re
import shutil
from typing import List, Dict, Tuple, Optional

class LaTeXTemplateValidator:
    """Validates and fixes LaTeX template structure issues"""
    
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
    
    def validate_and_fix_template(self, tex_file: str, auto_fix: bool = True) -> Dict[str, any]:
        """
        Validate LaTeX template structure and optionally fix issues
        
        Args:
            tex_file: Path to the LaTeX file
            auto_fix: Whether to automatically fix found issues
            
        Returns:
            Dictionary with validation results and fixes applied
        """
        if not os.path.exists(tex_file):
            return {"success": False, "error": f"File not found: {tex_file}"}
        
        # Reset state
        self.issues_found = []
        self.fixes_applied = []
        
        # Read the file
        try:
            with open(tex_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {"success": False, "error": f"Could not read file: {e}"}
        
        original_content = content
        
        # Run all validation checks
        content = self._check_document_structure(content, auto_fix)
        content = self._check_preamble_content(content, auto_fix)
        content = self._check_title_author_placement(content, auto_fix)
        content = self._check_abstract_placement(content, auto_fix)
        content = self._check_bibliography_setup(content, auto_fix)
        content = self._check_figure_references(content, auto_fix)
        content = self._check_section_structure(content, auto_fix)
        
        # Apply fixes if requested and changes were made
        if auto_fix and content != original_content:
            # Create backup
            backup_file = tex_file + '.structure_backup'
            shutil.copy2(tex_file, backup_file)
            
            # Write fixed content
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.fixes_applied.append(f"Created backup: {backup_file}")
            self.fixes_applied.append(f"Applied {len([f for f in self.fixes_applied if f.startswith('Fixed')])} structural fixes")
        
        return {
            "success": True,
            "issues_found": self.issues_found,
            "fixes_applied": self.fixes_applied,
            "needs_fixing": len(self.issues_found) > 0,
            "backup_created": auto_fix and content != original_content
        }
    
    def _check_document_structure(self, content: str, auto_fix: bool) -> str:
        """Check for proper \begin{document} ... \end{document} structure"""
        
        # Check if \begin{document} exists
        if not re.search(r'\\begin\{document\}', content):
            self.issues_found.append("Missing \\begin{document}")
            if auto_fix:
                # Find a good place to insert it (after preamble, before content)
                # Look for \maketitle, \title, or first section
                insertion_patterns = [
                    r'(\\maketitle)',
                    r'(\\title\{[^}]*\}\s*\\author\{[^}]*\})',
                    r'(\\begin\{abstract\})',
                    r'(\\section\{)'
                ]
                
                for pattern in insertion_patterns:
                    match = re.search(pattern, content)
                    if match:
                        insert_pos = match.start()
                        content = content[:insert_pos] + "\\begin{document}\n\n" + content[insert_pos:]
                        self.fixes_applied.append("Fixed: Added \\begin{document}")
                        break
        
        # Check if \end{document} exists
        if not re.search(r'\\end\{document\}', content):
            self.issues_found.append("Missing \\end{document}")
            if auto_fix:
                content += "\n\\end{document}\n"
                self.fixes_applied.append("Fixed: Added \\end{document}")
        
        return content
    
    def _check_preamble_content(self, content: str, auto_fix: bool) -> str:
        """Check that preamble content appears before \begin{document}"""
        
        begin_doc_match = re.search(r'\\begin\{document\}', content)
        if not begin_doc_match:
            return content
        
        begin_doc_pos = begin_doc_match.start()
        preamble = content[:begin_doc_pos]
        document_body = content[begin_doc_pos:]
        
        # Check for content that should be in preamble but appears in document body
        preamble_commands = [
            r'\\documentclass',
            r'\\usepackage',
            r'\\newcommand',
            r'\\renewcommand',
            r'\\input\{[^}]*\.sty\}',
            r'\\input\{[^}]*commands[^}]*\}'
        ]
        
        fixes_needed = []
        for cmd_pattern in preamble_commands:
            matches = list(re.finditer(cmd_pattern, document_body))
            if matches:
                for match in matches:
                    line_start = document_body.rfind('\n', 0, match.start()) + 1
                    line_end = document_body.find('\n', match.end())
                    if line_end == -1:
                        line_end = len(document_body)
                    
                    problematic_line = document_body[line_start:line_end]
                    self.issues_found.append(f"Preamble command in document body: {problematic_line.strip()}")
                    
                    if auto_fix:
                        fixes_needed.append((line_start, line_end, problematic_line))
        
        # Apply fixes (move commands to preamble)
        if auto_fix and fixes_needed:
            # Sort by position (reverse order to maintain positions)
            fixes_needed.sort(key=lambda x: x[0], reverse=True)
            
            moved_commands = []
            for line_start, line_end, line_content in fixes_needed:
                # Remove from document body
                document_body = document_body[:line_start] + document_body[line_end:]
                moved_commands.append(line_content)
            
            # Add to preamble
            preamble += '\n' + '\n'.join(moved_commands) + '\n'
            content = preamble + document_body
            
            self.fixes_applied.append(f"Fixed: Moved {len(fixes_needed)} preamble commands")
        
        return content
    
    def _check_title_author_placement(self, content: str, auto_fix: bool) -> str:
        """Check that \title, \author are before \begin{document} and \maketitle is after"""
        
        begin_doc_match = re.search(r'\\begin\{document\}', content)
        if not begin_doc_match:
            return content
        
        begin_doc_pos = begin_doc_match.start()
        preamble = content[:begin_doc_pos]
        document_body = content[begin_doc_pos:]
        
        # Check for \title and \author in document body (should be in preamble)
        title_in_body = re.search(r'\\title\{', document_body)
        author_in_body = re.search(r'\\author\{', document_body)
        
        if title_in_body or author_in_body:
            self.issues_found.append("\\title or \\author found in document body (should be in preamble)")
            
            if auto_fix:
                # Extract title and author from document body
                title_match = re.search(r'\\title\{[^}]*\}', document_body)
                author_match = re.search(r'\\author\{[^}]*\}', document_body)
                
                title_cmd = title_match.group(0) if title_match else ""
                author_cmd = author_match.group(0) if author_match else ""
                
                # Remove from document body
                if title_match:
                    document_body = document_body.replace(title_cmd, "")
                if author_match:
                    document_body = document_body.replace(author_cmd, "")
                
                # Add to preamble
                if title_cmd or author_cmd:
                    preamble += f"\n{title_cmd}\n{author_cmd}\n"
                    self.fixes_applied.append("Fixed: Moved \\title and \\author to preamble")
        
        # Check for \maketitle in preamble (should be in document body)
        maketitle_in_preamble = re.search(r'\\maketitle', preamble)
        if maketitle_in_preamble:
            self.issues_found.append("\\maketitle found in preamble (should be in document body)")
            
            if auto_fix:
                # Remove from preamble
                preamble = re.sub(r'\\maketitle\s*', '', preamble)
                
                # Add to document body (after \begin{document})
                begin_doc_line = re.search(r'\\begin\{document\}', document_body)
                if begin_doc_line:
                    insert_pos = begin_doc_line.end()
                    document_body = (document_body[:insert_pos] + 
                                   "\n\n\\maketitle\n" + 
                                   document_body[insert_pos:])
                    self.fixes_applied.append("Fixed: Moved \\maketitle to document body")
        
        return preamble + document_body
    
    def _check_abstract_placement(self, content: str, auto_fix: bool) -> str:
        """Check that abstract is properly placed in document body"""
        
        begin_doc_match = re.search(r'\\begin\{document\}', content)
        if not begin_doc_match:
            return content
        
        begin_doc_pos = begin_doc_match.start()
        preamble = content[:begin_doc_pos]
        
        # Check for abstract in preamble
        abstract_in_preamble = re.search(r'\\begin\{abstract\}', preamble)
        if abstract_in_preamble:
            self.issues_found.append("\\begin{abstract} found in preamble (should be in document body)")
            
            if auto_fix:
                # Extract abstract from preamble
                abstract_match = re.search(r'\\begin\{abstract\}.*?\\end\{abstract\}', preamble, re.DOTALL)
                if abstract_match:
                    abstract_content = abstract_match.group(0)
                    
                    # Remove from preamble
                    preamble = preamble.replace(abstract_content, "")
                    
                    # Add to document body (after \maketitle if present)
                    document_body = content[begin_doc_pos:]
                    maketitle_match = re.search(r'\\maketitle', document_body)
                    
                    if maketitle_match:
                        insert_pos = begin_doc_pos + maketitle_match.end()
                        content = (content[:insert_pos] + 
                                 f"\n\n{abstract_content}\n" + 
                                 content[insert_pos:])
                    else:
                        # Insert after \begin{document}
                        insert_pos = begin_doc_match.end()
                        content = (content[:insert_pos] + 
                                 f"\n\n{abstract_content}\n" + 
                                 content[insert_pos:])
                    
                    self.fixes_applied.append("Fixed: Moved abstract to document body")
        
        return content
    
    def _check_bibliography_setup(self, content: str, auto_fix: bool) -> str:
        """Check bibliography setup and references"""
        
        # Check for \bibliography command
        bib_command = re.search(r'\\bibliography\{([^}]+)\}', content)
        if bib_command:
            bib_file = bib_command.group(1)
            
            # Check if .bib extension is included (it shouldn't be)
            if bib_file.endswith('.bib'):
                self.issues_found.append(f"Bibliography command includes .bib extension: {bib_file}")
                if auto_fix:
                    new_bib_file = bib_file[:-4]  # Remove .bib
                    content = content.replace(f'\\bibliography{{{bib_file}}}', 
                                           f'\\bibliography{{{new_bib_file}}}')
                    self.fixes_applied.append(f"Fixed: Removed .bib extension from bibliography command")
        
        # Check for \bibliographystyle
        if not re.search(r'\\bibliographystyle\{', content):
            self.issues_found.append("Missing \\bibliographystyle command")
            if auto_fix:
                # Add before \bibliography if it exists, otherwise at end
                if bib_command:
                    insert_pos = bib_command.start()
                    content = (content[:insert_pos] + 
                             "\\bibliographystyle{iclr2025}\n" + 
                             content[insert_pos:])
                else:
                    content += "\n\\bibliographystyle{iclr2025}\n\\bibliography{references}\n"
                self.fixes_applied.append("Fixed: Added \\bibliographystyle command")
        
        return content
    
    def _check_figure_references(self, content: str, auto_fix: bool) -> str:
        """Check for proper figure references and labels"""
        
        # Find all \ref{} commands
        ref_matches = re.findall(r'\\ref\{([^}]+)\}', content)
        
        # Find all \label{} commands
        label_matches = re.findall(r'\\label\{([^}]+)\}', content)
        
        # Check for undefined references
        undefined_refs = set(ref_matches) - set(label_matches)
        if undefined_refs:
            for ref in undefined_refs:
                self.issues_found.append(f"Undefined reference: {ref}")
        
        # Check for figures without labels
        figure_blocks = re.findall(r'\\begin\{figure\}.*?\\end\{figure\}', content, re.DOTALL)
        for i, fig_block in enumerate(figure_blocks):
            if not re.search(r'\\label\{', fig_block):
                self.issues_found.append(f"Figure {i+1} missing \\label command")
                if auto_fix:
                    # Try to infer label from caption or use generic
                    caption_match = re.search(r'\\caption\{([^}]+)\}', fig_block)
                    if caption_match:
                        # Create label from caption
                        caption = caption_match.group(1)
                        label = re.sub(r'[^a-zA-Z0-9_]', '_', caption.lower())[:20]
                        label = f"fig:{label}"
                    else:
                        label = f"fig:figure_{i+1}"
                    
                    # Insert label after caption or at end of figure
                    if caption_match:
                        insert_pos = fig_block.find(caption_match.group(0)) + len(caption_match.group(0))
                        new_fig_block = (fig_block[:insert_pos] + 
                                       f"\n\\label{{{label}}}" + 
                                       fig_block[insert_pos:])
                    else:
                        # Insert before \end{figure}
                        new_fig_block = fig_block.replace("\\end{figure}", 
                                                        f"\\label{{{label}}}\n\\end{{figure}}")
                    
                    content = content.replace(fig_block, new_fig_block)
                    self.fixes_applied.append(f"Fixed: Added label {label} to figure {i+1}")
        
        return content
    
    def _check_section_structure(self, content: str, auto_fix: bool) -> str:
        """Check section hierarchy and structure"""
        
        # Find all section commands
        sections = re.findall(r'\\((?:sub)*section)\{([^}]+)\}', content)
        
        if not sections:
            self.issues_found.append("No sections found in document")
            return content
        
        # Check for proper hierarchy
        section_levels = {'section': 1, 'subsection': 2, 'subsubsection': 3}
        prev_level = 0
        
        for section_type, section_title in sections:
            current_level = section_levels.get(section_type, 1)
            
            # Check for skipped levels (e.g., section -> subsubsection)
            if current_level > prev_level + 1:
                self.issues_found.append(f"Section hierarchy skip: {section_type} '{section_title}' after level {prev_level}")
            
            prev_level = current_level
        
        # Check for sections without labels
        for section_type, section_title in sections:
            section_pattern = f"\\\\{section_type}\\{{{re.escape(section_title)}\\}}"
            section_match = re.search(section_pattern, content)
            if section_match:
                # Look for \label within next few lines
                next_content = content[section_match.end():section_match.end()+200]
                if not re.search(r'\\label\{', next_content):
                    self.issues_found.append(f"Section '{section_title}' missing \\label")
                    
                    if auto_fix:
                        # Create label from section title
                        label = re.sub(r'[^a-zA-Z0-9_]', '_', section_title.lower())
                        label = f"sec:{label}"
                        
                        # Insert label after section command
                        insert_pos = section_match.end()
                        content = (content[:insert_pos] + 
                                 f"\n\\label{{{label}}}" + 
                                 content[insert_pos:])
                        self.fixes_applied.append(f"Fixed: Added label {label} to section '{section_title}'")
        
        return content
    
    def print_validation_report(self, results: Dict[str, any]):
        """Print a formatted validation report"""
        print("\n" + "="*60)
        print("📋 LATEX TEMPLATE VALIDATION REPORT")
        print("="*60)
        
        if not results["success"]:
            print(f"❌ Validation failed: {results.get('error', 'Unknown error')}")
            return
        
        if not results["needs_fixing"]:
            print("✅ Template structure is valid - no issues found!")
            return
        
        print(f"⚠️  Found {len(results['issues_found'])} structural issues:")
        for i, issue in enumerate(results['issues_found'], 1):
            print(f"  {i}. {issue}")
        
        if results['fixes_applied']:
            print(f"\n🔧 Applied {len(results['fixes_applied'])} fixes:")
            for i, fix in enumerate(results['fixes_applied'], 1):
                print(f"  {i}. {fix}")
        
        if results.get('backup_created'):
            print("\n💾 Backup created before applying fixes")
        
        print("="*60)


def main():
    """Command line interface for the validator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate and fix LaTeX template structure")
    parser.add_argument("tex_file", help="Path to LaTeX file to validate")
    parser.add_argument("--no-fix", action="store_true", help="Only validate, don't fix issues")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    
    args = parser.parse_args()
    
    validator = LaTeXTemplateValidator()
    results = validator.validate_and_fix_template(args.tex_file, auto_fix=not args.no_fix)
    
    if not args.quiet:
        validator.print_validation_report(results)
    
    # Exit with non-zero code if issues were found
    exit_code = 0 if not results.get("needs_fixing", True) else 1
    exit(exit_code)


if __name__ == "__main__":
    main() 