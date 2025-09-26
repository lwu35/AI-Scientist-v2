#!/usr/bin/env python3

import os
import sys
import shutil

# Add TinyTeX to PATH before importing anything else
tinytex_path = os.path.expanduser("~/Library/TinyTeX/bin/universal-darwin")
if os.path.exists(tinytex_path):
    os.environ['PATH'] = f"{tinytex_path}:{os.environ.get('PATH', '')}"

from ai_scientist.perform_icbinb_writeup import perform_writeup, gather_citations
from ai_scientist.perform_llm_review import perform_review, load_paper
from ai_scientist.perform_vlm_review import perform_imgs_cap_ref_review
from ai_scientist.llm import create_client
import json
import os.path as osp
import re

def find_pdf_path_for_review(idea_dir):
    """Find the most recent PDF file for review"""
    pdf_files = [f for f in os.listdir(idea_dir) if f.endswith(".pdf")]
    reflection_pdfs = [f for f in pdf_files if "reflection" in f]
    pdf_path = None
    
    if reflection_pdfs:
        # First check if there's a final version
        final_pdfs = [f for f in reflection_pdfs if "final" in f.lower()]
        if final_pdfs:
            pdf_path = osp.join(idea_dir, final_pdfs[0])
        else:
            # Try to find numbered reflections
            reflection_nums = []
            for f in reflection_pdfs:
                match = re.search(r"reflection[_.]?(\d+)", f)
                if match:
                    reflection_nums.append((int(match.group(1)), f))

            if reflection_nums:
                # Get the file with the highest reflection number
                highest_reflection = max(reflection_nums, key=lambda x: x[0])
                pdf_path = osp.join(idea_dir, highest_reflection[1])
            else:
                # Fall back to the first reflection PDF if no numbers found
                pdf_path = osp.join(idea_dir, reflection_pdfs[0])
    elif pdf_files:
        # If no reflection PDFs, use any available PDF
        pdf_path = osp.join(idea_dir, pdf_files[0])
    
    return pdf_path

def restore_corrupted_template(latex_dir, base_template_dir):
    """Restore the corrupted template.tex from the base template"""
    corrupted_template = os.path.join(latex_dir, "template.tex")
    base_template = os.path.join(base_template_dir, "template.tex")
    
    if not os.path.exists(base_template):
        print(f"❌ Base template not found at: {base_template}")
        return False
    
    # Read the base template
    with open(base_template, 'r') as f:
        template_content = f.read()
    
    # Add siunitx package to fix \num and \SI commands
    if '\\usepackage{siunitx}' not in template_content:
        # Find the best place to insert siunitx (after amsmath packages)
        lines = template_content.split('\n')
        insert_idx = -1
        for i, line in enumerate(lines):
            if 'amsmath' in line or 'amsfonts' in line:
                insert_idx = i + 1
        
        if insert_idx > 0:
            lines.insert(insert_idx, '\\usepackage{siunitx}')
            template_content = '\n'.join(lines)
        else:
            # Fallback: insert after documentclass
            template_content = template_content.replace(
                '\\documentclass{article}',
                '\\documentclass{article}\n\\usepackage{siunitx}'
            )
    
    # Write the restored template
    with open(corrupted_template, 'w') as f:
        f.write(template_content)
    
    print("✅ Restored corrupted template.tex with siunitx package")
    return True

def main():
    # Target the specific failed experiment
    experiment_dir = "experiments/2025-09-25_23-36-32_emotional_intelligence_llms_attempt_0"
    base_template_dir = "ai_scientist/blank_icbinb_latex"
    
    if not os.path.exists(experiment_dir):
        print(f"Error: Experiment directory {experiment_dir} not found!")
        print("Available experiments:")
        for exp in os.listdir("experiments"):
            if os.path.isdir(os.path.join("experiments", exp)):
                print(f"  - {exp}")
        sys.exit(1)
    
    print(f"🎯 Resuming experiment: {experiment_dir}")
    print(f"🔧 Using pdflatex from: {tinytex_path}")
    
    # Check if pdflatex is available
    pdflatex_path = shutil.which('pdflatex')
    if pdflatex_path:
        print(f"✅ pdflatex found at: {pdflatex_path}")
    else:
        print("❌ pdflatex not found in PATH!")
        sys.exit(1)
    
    # Check what stage we're at
    latex_dir = os.path.join(experiment_dir, "latex")
    citations_file = os.path.join(experiment_dir, "cached_citations.bib")
    
    if os.path.exists(latex_dir):
        print("✅ LaTeX files already exist - checking for corruption...")
        
        # Check if template.tex is corrupted (missing \documentclass)
        template_file = os.path.join(latex_dir, "template.tex")
        if os.path.exists(template_file):
            with open(template_file, 'r') as f:
                template_content = f.read()
            
            if '\\documentclass' not in template_content:
                print("🔧 Detected corrupted template.tex - restoring from base template...")
                if not restore_corrupted_template(latex_dir, base_template_dir):
                    print("❌ Failed to restore template")
                    sys.exit(1)
            else:
                print("✅ Template appears intact")
        
        # Load existing citations
        citations_text = None
        if os.path.exists(citations_file):
            with open(citations_file, 'r') as f:
                citations_text = f.read()
            print("✅ Using existing citations")
        else:
            print("⚠️ No cached citations found, will gather new ones")
    else:
        print("📚 Starting from citation gathering...")
        citations_text = None
    
    # If we don't have citations, gather them
    if not citations_text:
        print("📚 Gathering citations...")
        citations_text = gather_citations(
            experiment_dir,
            num_cite_rounds=20,
            small_model="gpt-4o-2024-11-20",
        )
    
    # Additional template fixes
    latex_file = os.path.join(experiment_dir, "latex", "template.tex")
    if os.path.exists(latex_file):
        print("🔧 Applying additional template fixes...")
        with open(latex_file, 'r') as f:
            content = f.read()
        
        fixes_applied = []
        
        # Fix bibliography reference
        if '\\bibliography{iclr2025}' in content:
            content = content.replace('\\bibliography{iclr2025}', '\\bibliography{references}')
            fixes_applied.append("bibliography reference")
        
        # Fix missing style file references
        if 'iclr2025_conference.sty' in content:
            content = content.replace('\\usepackage{iclr2025_conference}', '\\usepackage{iclr2025}')
            fixes_applied.append("conference style file")
        
        # Ensure siunitx package is present
        if '\\usepackage{siunitx}' not in content:
            # Find the best place to insert siunitx
            if '\\usepackage{amsmath}' in content:
                content = content.replace('\\usepackage{amsmath}', '\\usepackage{amsmath}\n\\usepackage{siunitx}')
                fixes_applied.append("siunitx package")
            elif '\\documentclass{article}' in content:
                content = content.replace('\\documentclass{article}', '\\documentclass{article}\n\\usepackage{siunitx}')
                fixes_applied.append("siunitx package")
        
        # Add missing caption package if needed
        if '\\captionof' in content and '\\usepackage{caption}' not in content:
            # Find last usepackage line and insert after it
            lines = content.split('\n')
            last_usepackage_idx = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('\\usepackage'):
                    last_usepackage_idx = i
            if last_usepackage_idx >= 0:
                lines.insert(last_usepackage_idx + 1, '\\usepackage{caption}')
                content = '\n'.join(lines)
                fixes_applied.append("caption package")
        
        if fixes_applied:
            with open(latex_file, 'w') as f:
                f.write(content)
            print(f"✅ Fixed: {', '.join(fixes_applied)}")
        else:
            print("✅ Template already correct")

    # Remove the corrupted final reflection PDF that's causing issues
    corrupted_pdf = os.path.join(experiment_dir, "2025-09-25_23-36-32_emotional_intelligence_llms_attempt_0_reflection_final_page_limit.pdf")
    if os.path.exists(corrupted_pdf):
        os.remove(corrupted_pdf)
        print("🗑️ Removed corrupted final reflection PDF")

    # Perform writeup (this will regenerate the PDF properly)
    print("📝 Starting/resuming writeup...")
    success = perform_writeup(
        base_folder=experiment_dir,
        citations_text=citations_text,
        big_model="gpt-4o-2024-11-20",
        page_limit=4,
    )
    
    if success:
        print(f"🎉 Writeup completed successfully!")
        
        # Check if PDF was created
        pdf_files = [f for f in os.listdir(experiment_dir) if f.endswith('.pdf')]
        if pdf_files:
            print(f"📄 Generated PDF files: {pdf_files}")
            
            # Now perform the review that was supposed to happen next
            print("🔍 Starting paper review...")
            pdf_path = find_pdf_path_for_review(experiment_dir)
            if pdf_path and os.path.exists(pdf_path):
                try:
                    print(f"📄 Reviewing paper at: {pdf_path}")
                    paper_content = load_paper(pdf_path)
                    client, client_model = create_client("gpt-4o-2024-11-20")
                    review_text = perform_review(paper_content, client_model, client)
                    review_img_cap_ref = perform_imgs_cap_ref_review(
                        client, client_model, pdf_path
                    )
                    with open(osp.join(experiment_dir, "review_text.txt"), "w") as f:
                        f.write(json.dumps(review_text, indent=4))
                    with open(osp.join(experiment_dir, "review_img_cap_ref.json"), "w") as f:
                        json.dump(review_img_cap_ref, f, indent=4)
                    print("✅ Paper review completed!")
                except Exception as e:
                    print(f"⚠️ Review failed: {e}")
                    print("📄 But PDF was generated successfully!")
            else:
                print("⚠️ Could not find PDF for review")
        else:
            print("❌ No PDF files found after writeup")
    else:
        print("❌ Writeup failed. Check the logs for details.")
        return False
    
    print("🏁 Resume completed successfully!")
    return True

if __name__ == "__main__":
    main() 