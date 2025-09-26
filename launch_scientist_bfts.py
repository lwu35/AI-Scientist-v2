import os.path as osp
import json
import argparse
import shutil
import torch
import os
import re
import sys
import signal
from datetime import datetime
from ai_scientist.llm import create_client

from contextlib import contextmanager
from ai_scientist.treesearch.perform_experiments_bfts_with_agentmanager import (
    perform_experiments_bfts,
)
from ai_scientist.treesearch.bfts_utils import (
    idea_to_markdown,
    edit_bfts_config_file,
)
from ai_scientist.perform_plotting import aggregate_plots
from ai_scientist.perform_writeup import perform_writeup
from ai_scientist.perform_icbinb_writeup import (
    perform_writeup as perform_icbinb_writeup,
    gather_citations,
)

# Import LaTeX validation system
try:
    from ai_scientist.utils.latex_helper import LaTeXPackageManager, get_writeup_constraints_prompt
    LATEX_VALIDATION_AVAILABLE = True
except ImportError:
    print("⚠️  LaTeX validation system not available - using basic compilation")
    LATEX_VALIDATION_AVAILABLE = False
from ai_scientist.perform_llm_review import perform_review, load_paper
from ai_scientist.perform_vlm_review import perform_imgs_cap_ref_review
from ai_scientist.utils.token_tracker import token_tracker


def print_time():
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def cleanup_processes():
    """Clean up all child processes"""
    print("Start cleaning up processes")
    try:
        import psutil
        # Get the current process and all its children
        current_process = psutil.Process()
        children = current_process.children(recursive=True)

        # First try graceful termination
        for child in children:
            try:
                child.send_signal(signal.SIGTERM)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Wait briefly for processes to terminate
        gone, alive = psutil.wait_procs(children, timeout=3)

        # If any processes remain, force kill them
        for process in alive:
            try:
                process.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        print(f"Cleaned up {len(gone)} processes, force killed {len(alive)} processes")
    except Exception as e:
        print(f"Error during process cleanup: {e}")


def signal_handler(signum, frame):
    """Handle interruption signals gracefully"""
    print(f"\n🛑 Received signal {signum}. Cleaning up...")
    cleanup_processes()
    sys.exit(1)


def save_token_tracker(idea_dir):
    with open(osp.join(idea_dir, "token_tracker.json"), "w") as f:
        json.dump(token_tracker.get_summary(), f)
    with open(osp.join(idea_dir, "token_tracker_interactions.json"), "w") as f:
        json.dump(token_tracker.get_interactions(), f)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run AI scientist experiments")
    parser.add_argument(
        "--writeup-type",
        type=str,
        default="icbinb",
        choices=["normal", "icbinb"],
        help="Type of writeup to generate (normal=8 page, icbinb=4 page)",
    )
    parser.add_argument(
        "--load_ideas",
        type=str,
        default="ideas/i_cant_believe_its_not_better.json",
        help="Path to a JSON file containing pregenerated ideas",
    )
    parser.add_argument(
        "--load_code",
        action="store_true",
        help="If set, load a Python file with same name as ideas file but .py extension",
    )
    parser.add_argument(
        "--idea_idx",
        type=int,
        default=0,
        help="Index of the idea to run",
    )
    parser.add_argument(
        "--add_dataset_ref",
        action="store_true",
        help="If set, add a HF dataset reference to the idea",
    )
    parser.add_argument(
        "--writeup-retries",
        type=int,
        default=3,
        help="Number of writeup attempts to try",
    )
    parser.add_argument(
        "--attempt_id",
        type=int,
        default=0,
        help="Attempt ID, used to distinguish same idea in different attempts in parallel runs",
    )
    parser.add_argument(
        "--model_agg_plots",
        type=str,
        default="o3-mini-2025-01-31",
        help="Model to use for plot aggregation",
    )
    parser.add_argument(
        "--model_writeup",
        type=str,
        default="o1-preview-2024-09-12",
        help="Model to use for writeup",
    )
    parser.add_argument(
        "--model_citation",
        type=str,
        default="gpt-4o-2024-11-20",
        help="Model to use for citation gathering",
    )
    parser.add_argument(
        "--num_cite_rounds",
        type=int,
        default=20,
        help="Number of citation rounds to perform",
    )
    parser.add_argument(
        "--model_review",
        type=str,
        default="gpt-4o-2024-11-20",
        help="Model to use for review main text and captions",
    )
    parser.add_argument(
        "--skip_writeup",
        action="store_true",
        help="If set, skip the writeup process",
    )
    parser.add_argument(
        "--skip_review",
        action="store_true",
        help="If set, skip the review process",
    )
    parser.add_argument(
        "--gpu_ids",
        type=str,
        default=None,
        help="Comma-separated list of GPU IDs to use (e.g., '0,1,2'). If not specified, all available GPUs will be used.",
    )
    parser.add_argument(
        "--force_cpu",
        action="store_true",
        help="Force CPU-only mode, even if GPUs are available",
    )
    parser.add_argument(
        "--disable_latex_validation",
        action="store_true",
        help="Disable LaTeX validation and auto-fixing features",
    )
    return parser.parse_args()


def validate_gpu_setup():
    """Validate GPU setup and provide detailed information"""
    print("\n🔍 GPU Setup Validation:")
    print("-" * 40)
    
    # Check CUDA_VISIBLE_DEVICES
    cuda_env = os.environ.get("CUDA_VISIBLE_DEVICES", "Not set")
    print(f"CUDA_VISIBLE_DEVICES: {cuda_env}")
    
    # Check nvidia-smi
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, check=True
        )
        print("nvidia-smi GPUs:")
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                print(f"  {line}")
    except Exception as e:
        print(f"nvidia-smi error: {e}")
    
    # Check torch CUDA
    try:
        torch_available = torch.cuda.is_available()
        torch_count = torch.cuda.device_count()
        print(f"PyTorch CUDA available: {torch_available}")
        print(f"PyTorch GPU count: {torch_count}")
        if torch_count > 0:
            for i in range(torch_count):
                try:
                    name = torch.cuda.get_device_name(i)
                    print(f"  GPU {i}: {name}")
                except:
                    print(f"  GPU {i}: <name unavailable>")
    except Exception as e:
        print(f"PyTorch CUDA error: {e}")
    
    print("-" * 40)


def get_available_gpus(gpu_ids=None):
    """Get available GPUs using the same method as BFTS system"""
    if gpu_ids is not None:
        return [int(gpu_id) for gpu_id in gpu_ids.split(",")]
    
    # Use the same detection method as parallel_agent.py
    import subprocess
    try:
        # First try using nvidia-smi (same as BFTS)
        nvidia_smi = subprocess.run(
            ["nvidia-smi", "--query-gpu=gpu_name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=True,
        )
        gpus = nvidia_smi.stdout.strip().split("\n")
        gpu_count = len(gpus)
        return list(range(gpu_count))
    except (subprocess.SubprocessError, FileNotFoundError):
        # Fallback to torch method
        try:
            return list(range(torch.cuda.device_count()))
        except:
            # Final fallback to environment variable
            cuda_visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES")
            if cuda_visible_devices:
                devices = [d for d in cuda_visible_devices.split(",") if d and d != "-1"]
                return list(range(len(devices)))
            return []


def find_pdf_path_for_review(idea_dir):
    pdf_files = [f for f in os.listdir(idea_dir) if f.endswith(".pdf")]
    reflection_pdfs = [f for f in pdf_files if "reflection" in f]
    pdf_path = None
    
    if reflection_pdfs:
        # First check if there's a final version
        final_pdfs = [f for f in reflection_pdfs if "final" in f.lower()]
        if final_pdfs:
            # Use the final version if available
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


@contextmanager
def redirect_stdout_stderr_to_file(log_file_path):
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    log = open(log_file_path, "a")
    sys.stdout = log
    sys.stderr = log
    try:
        yield
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        log.close()


if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    args = parse_arguments()
    os.environ["AI_SCIENTIST_ROOT"] = os.path.dirname(os.path.abspath(__file__))
    print(f"Set AI_SCIENTIST_ROOT to {os.environ['AI_SCIENTIST_ROOT']}")

    # Display LaTeX validation status
    if LATEX_VALIDATION_AVAILABLE and not args.disable_latex_validation:
        print("🔧 LaTeX validation system: ENABLED")
        print("   - Pre-writeup constraint generation")
        print("   - Post-writeup validation checks") 
        print("   - Automatic issue fixing during compilation")
    else:
        reason = "disabled by --disable_latex_validation" if args.disable_latex_validation else "not available"
        print(f"⚠️  LaTeX validation system: DISABLED ({reason})")

    # Validate GPU setup before proceeding
    validate_gpu_setup()

    # Check available GPUs and configure GPU usage
    if args.force_cpu:
        print("🖥️  Force CPU mode enabled - disabling GPU usage")
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        available_gpus = []
    else:
        available_gpus = get_available_gpus(args.gpu_ids)
        if available_gpus:
            print(f"🎮 Using GPUs: {available_gpus}")
            # Set CUDA_VISIBLE_DEVICES for the entire process tree
            os.environ["CUDA_VISIBLE_DEVICES"] = ",".join(map(str, available_gpus))
        else:
            print("🖥️  No GPUs detected - falling back to CPU mode")
            os.environ["CUDA_VISIBLE_DEVICES"] = ""

    with open(args.load_ideas, "r") as f:
        ideas = json.load(f)
        print(f"Loaded {len(ideas)} pregenerated ideas from {args.load_ideas}")

    idea = ideas[args.idea_idx]

    date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    idea_dir = f"experiments/{date}_{idea['Name']}_attempt_{args.attempt_id}"
    print(f"Results will be saved in {idea_dir}")
    os.makedirs(idea_dir, exist_ok=True)

    # Convert idea json to markdown file
    idea_path_md = osp.join(idea_dir, "idea.md")

    # If load_code is True, get the Python file with same name as JSON
    code = None
    if args.load_code:
        code_path = args.load_ideas.rsplit(".", 1)[0] + ".py"
        if os.path.exists(code_path):
            with open(code_path, "r") as f:
                code = f.read()
        else:
            print(f"Warning: Code file {code_path} not found")
    else:
        code_path = None

    idea_to_markdown(ideas[args.idea_idx], idea_path_md, code_path)

    dataset_ref_code = None
    if args.add_dataset_ref:
        dataset_ref_path = "hf_dataset_reference.py"
        if os.path.exists(dataset_ref_path):
            with open(dataset_ref_path, "r") as f:
                dataset_ref_code = f.read()
        else:
            print(f"Warning: Dataset reference file {dataset_ref_path} not found")
            dataset_ref_code = None

    if dataset_ref_code is not None and code is not None:
        added_code = dataset_ref_code + "\n" + code
    elif dataset_ref_code is not None and code is None:
        added_code = dataset_ref_code
    elif dataset_ref_code is None and code is not None:
        added_code = code
    else:
        added_code = None

    print(added_code)

    # Add code to idea json if it was loaded
    if added_code is not None:
        ideas[args.idea_idx]["Code"] = added_code

    # Store raw idea json
    idea_path_json = osp.join(idea_dir, "idea.json")
    with open(idea_path_json, "w") as f:
        json.dump(ideas[args.idea_idx], f, indent=4)

    config_path = "bfts_config.yaml"
    
    # Prepare GPU information for BFTS system
    gpu_info = {
        "available_gpus": available_gpus,
        "force_cpu": args.force_cpu,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", "")
    }
    
    idea_config_path = edit_bfts_config_file(
        config_path,
        idea_dir,
        idea_path_json,
        gpu_info,
    )

    perform_experiments_bfts(idea_config_path)
    experiment_results_dir = osp.join(idea_dir, "logs/0-run/experiment_results")
    if os.path.exists(experiment_results_dir):
        shutil.copytree(
            experiment_results_dir,
            osp.join(idea_dir, "experiment_results"),
            dirs_exist_ok=True,
        )

    aggregate_plots(base_folder=idea_dir, model=args.model_agg_plots)

    shutil.rmtree(osp.join(idea_dir, "experiment_results"))

    save_token_tracker(idea_dir)

    if not args.skip_writeup:
        writeup_success = False
        citations_text = gather_citations(
            idea_dir,
            num_cite_rounds=args.num_cite_rounds,
            small_model=args.model_citation,
        )
        
        # Fix bibliography reference to prevent citation issues
        latex_file = osp.join(idea_dir, "latex", "template.tex")
        if osp.exists(latex_file):
            print("🔧 Checking bibliography reference in LaTeX template...")
            with open(latex_file, 'r') as f:
                content = f.read()
            if '\\bibliography{iclr2025}' in content:
                print("📋 Fixing bibliography reference: iclr2025 → references")
                content = content.replace('\\bibliography{iclr2025}', '\\bibliography{references}')
                with open(latex_file, 'w') as f:
                    f.write(content)
                print("✅ Bibliography reference fixed - citations should now work properly")
            else:
                print("✅ Bibliography reference already correct")
        
        # Pre-writeup LaTeX validation and constraints
        if LATEX_VALIDATION_AVAILABLE and not args.disable_latex_validation:
            print("\n🔍 Performing pre-writeup LaTeX validation...")
            try:
                constraints_prompt = get_writeup_constraints_prompt(idea_dir)
                print("📋 Generated LaTeX constraints for writeup models:")
                print("   - Available figures and citations identified")
                print("   - Validation rules prepared")
                print("   - Auto-fix system ready")
                
                # Optionally save constraints to a file for debugging
                constraints_file = osp.join(idea_dir, "latex_constraints.txt")
                with open(constraints_file, 'w') as f:
                    f.write(constraints_prompt)
                print(f"   - Constraints saved to: {constraints_file}")
                
            except Exception as e:
                print(f"⚠️  LaTeX validation setup failed: {e}")
                print("   Proceeding with standard writeup process")
        else:
            print("⚠️  LaTeX validation not available - using standard process")
        
        for attempt in range(args.writeup_retries):
            print(f"Writeup attempt {attempt+1} of {args.writeup_retries}")
            if args.writeup_type == "normal":
                writeup_success = perform_writeup(
                    base_folder=idea_dir,
                    big_model=args.model_writeup,
                    page_limit=8,
                    citations_text=citations_text,
                )
            else:
                writeup_success = perform_icbinb_writeup(
                    base_folder=idea_dir,
                    big_model=args.model_writeup,
                    page_limit=4,
                    citations_text=citations_text,
                )
            if writeup_success:
                break

        if not writeup_success:
            print("Writeup process did not complete successfully after all retries.")
        else:
            # Post-writeup LaTeX validation
            if LATEX_VALIDATION_AVAILABLE and not args.disable_latex_validation:
                print("\n🔍 Performing post-writeup LaTeX validation...")
                try:
                    manager = LaTeXPackageManager()
                    latex_file = osp.join(idea_dir, "latex", "template.tex")
                    
                    if osp.exists(latex_file):
                        issues = manager.validate_latex_file(latex_file)
                        total_issues = sum(len(issue_list) for issue_list in issues.values() if isinstance(issue_list, list))
                        
                        if total_issues > 0:
                            print(f"⚠️  Found {total_issues} LaTeX issues in generated writeup:")
                            if issues['missing_figures']:
                                print(f"   📷 Missing figures: {len(issues['missing_figures'])}")
                            if issues['missing_style_files']:
                                print(f"   📄 Missing style files: {len(issues['missing_style_files'])}")
                            if issues['undefined_labels']:
                                print(f"   🏷️  Undefined labels: {len(issues['undefined_labels'])}")
                            if issues['undefined_citations']:
                                print(f"   📚 Undefined citations: {len(issues['undefined_citations'])}")
                            
                            print("   🔧 Auto-fix will be applied during compilation")
                        else:
                            print("✅ LaTeX validation passed - no issues found!")
                    
                except Exception as e:
                    print(f"⚠️  Post-writeup validation failed: {e}")
            
            print("✅ Writeup process completed successfully!")

    save_token_tracker(idea_dir)

    if not args.skip_review and not args.skip_writeup:
        # Perform paper review if the paper exists
        pdf_path = find_pdf_path_for_review(idea_dir)
        if pdf_path and os.path.exists(pdf_path):
            print("Paper found at: ", pdf_path)
            paper_content = load_paper(pdf_path)
            client, client_model = create_client(args.model_review)
            review_text = perform_review(paper_content, client_model, client)
            review_img_cap_ref = perform_imgs_cap_ref_review(
                client, client_model, pdf_path
            )
            with open(osp.join(idea_dir, "review_text.txt"), "w") as f:
                f.write(json.dumps(review_text, indent=4))
            with open(osp.join(idea_dir, "review_img_cap_ref.json"), "w") as f:
                json.dump(review_img_cap_ref, f, indent=4)
            print("Paper review completed.")

    cleanup_processes()

    # Finally, terminate the current process
    # current_process.send_signal(signal.SIGTERM)
    # try:
    #     current_process.wait(timeout=3)
    # except psutil.TimeoutExpired:
    #     current_process.kill()

    # exit the program
    sys.exit(0)
