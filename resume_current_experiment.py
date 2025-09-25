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

def main():
    # Your current experiment directory (the most recent one)
    experiment_dir = "experiments/2025-09-24_18-43-46_multimodal_memory_augmentation_attempt_0"
    
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
        print("✅ LaTeX files already exist - resuming from compilation step")
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
            small_model="gpt-4o-2024-05-13",  # Match your original parameters
        )
    
    # Fix bibliography reference and other template issues
    latex_file = os.path.join(experiment_dir, "latex", "template.tex")
    if os.path.exists(latex_file):
        print("🔧 Checking template issues...")
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
        
        # Add missing caption package if needed
        if '\\captionof' in content and '\\usepackage{caption}' not in content:
            # Find last usepackage line and insert after it
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('\\usepackage'):
                    last_usepackage_idx = i
            if 'last_usepackage_idx' in locals():
                lines.insert(last_usepackage_idx + 1, '\\usepackage{caption}')
                content = '\n'.join(lines)
                fixes_applied.append("caption package")
        
        if fixes_applied:
            with open(latex_file, 'w') as f:
                f.write(content)
            print(f"✅ Fixed: {', '.join(fixes_applied)}")
        else:
            print("✅ Template already correct")

    # Perform writeup (this will use existing LaTeX files if they exist)
    print("📝 Starting/resuming writeup...")
    success = perform_writeup(
        base_folder=experiment_dir,
        citations_text=citations_text,
        big_model="o1",  # Match your original parameters
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
                print(f"📄 Reviewing paper at: {pdf_path}")
                paper_content = load_paper(pdf_path)
                client, client_model = create_client("gpt-4o-2024-05-13")  # Match your original parameters
                review_text = perform_review(paper_content, client_model, client)
                review_img_cap_ref = perform_imgs_cap_ref_review(
                    client, client_model, pdf_path
                )
                with open(osp.join(experiment_dir, "review_text.txt"), "w") as f:
                    f.write(json.dumps(review_text, indent=4))
                with open(osp.join(experiment_dir, "review_img_cap_ref.json"), "w") as f:
                    json.dump(review_img_cap_ref, f, indent=4)
                print("✅ Paper review completed!")
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