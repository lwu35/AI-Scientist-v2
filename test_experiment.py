#!/usr/bin/env python3
"""
Efficient test script for AI Scientist experiments.
This script validates the pipeline without running full experiments.
"""

import os
import sys
import json
import shutil
import subprocess
import argparse
from datetime import datetime

def test_basic_setup():
    """Test basic environment and dependencies"""
    print(f"\n🔧 Testing Basic Setup")
    print("-" * 40)
    
    # Test imports
    try:
        from ai_scientist.llm import create_client
        from ai_scientist.treesearch.bfts_utils import idea_to_markdown, edit_bfts_config_file
        from ai_scientist.perform_plotting import aggregate_plots
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test API keys
    api_keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
    }
    
    configured_keys = [k for k, v in api_keys.items() if v]
    if configured_keys:
        print(f"✅ API keys configured: {', '.join(configured_keys)}")
    else:
        print("⚠️ No API keys found - some models may not work")
    
    # Test GPU availability
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            print(f"✅ {gpu_count} GPUs available")
        else:
            print("⚠️ No GPUs available - will use CPU (slower)")
    except ImportError:
        print("⚠️ PyTorch not available - GPU detection skipped")
    
    return True

def test_idea_loading(ideas_file="ai_scientist/ideas/i_cant_believe_its_not_better.json", idea_idx=0):
    """Test idea file loading and processing"""
    print(f"\n📝 Testing Idea Loading")
    print("-" * 40)
    
    try:
        if not os.path.exists(ideas_file):
            print(f"❌ Ideas file not found: {ideas_file}")
            return False
        
        with open(ideas_file, "r") as f:
            ideas = json.load(f)
        
        print(f"✅ Loaded {len(ideas)} ideas from {ideas_file}")
        
        if idea_idx >= len(ideas):
            print(f"❌ Idea index {idea_idx} out of range (0-{len(ideas)-1})")
            return False
        
        idea = ideas[idea_idx]
        
        # Check for standard AI Scientist format
        standard_fields = ["Name", "Experiment", "Interestingness", "Feasibility", "Novelty"]
        # Check for alternative format
        alternative_fields = ["Name", "Title", "Abstract", "Experiments"]
        
        has_standard = all(field in idea for field in standard_fields)
        has_alternative = all(field in idea for field in alternative_fields)
        
        if not has_standard and not has_alternative:
            missing_standard = [field for field in standard_fields if field not in idea]
            missing_alternative = [field for field in alternative_fields if field not in idea]
            print(f"❌ Idea doesn't match expected format")
            print(f"   Missing for standard format: {missing_standard}")
            print(f"   Missing for alternative format: {missing_alternative}")
            return False
        
        if has_standard:
            print(f"✅ Using standard AI Scientist format")
        else:
            print(f"✅ Using alternative research proposal format")
        
        print(f"✅ Selected idea: '{idea['Name']}'")
        print(f"✅ All required fields present")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_config_creation(ideas_file="ai_scientist/ideas/i_cant_believe_its_not_better.json", idea_idx=0):
    """Test configuration file creation"""
    print(f"\n⚙️ Testing Configuration Creation")
    print("-" * 40)
    
    try:
        from ai_scientist.treesearch.bfts_utils import edit_bfts_config_file
        
        # Load ideas
        with open(ideas_file, "r") as f:
            ideas = json.load(f)
        idea = ideas[idea_idx]
        
        # Create temporary test directory
        test_dir = f"test_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(test_dir, exist_ok=True)
        
        # Create temporary idea file
        idea_path = os.path.join(test_dir, "idea.json")
        with open(idea_path, "w") as f:
            json.dump(idea, f, indent=4)
        
        # Test config creation
        if os.path.exists("test_experiment_config.yaml"):
            config_path = edit_bfts_config_file(
                "test_experiment_config.yaml",
                test_dir,
                idea_path
            )
            print(f"✅ Configuration created: {config_path}")
            
            # Cleanup
            shutil.rmtree(test_dir)
            return True
        else:
            print("❌ test_experiment_config.yaml not found")
            shutil.rmtree(test_dir)
            return False
            
    except Exception as e:
        print(f"❌ Configuration creation error: {e}")
        # Cleanup on error
        if 'test_dir' in locals() and os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        return False

def test_llm_connectivity():
    """Test LLM API connectivity"""
    print(f"\n🤖 Testing LLM Connectivity")
    print("-" * 40)
    
    try:
        from ai_scientist.llm import create_client, get_response_from_llm
        
        # Test different models
        test_models = [
            "gpt-4o-2024-11-20",
            "claude-3-5-sonnet-20241022",
            "o3-mini-2025-01-31",
            "o3",
            "gpt-5",
            "gpt-5-mini",
        ]
        
        working_models = []
        for model in test_models:
            try:
                client, client_model = create_client(model)
                # Simple test query
                response, _ = get_response_from_llm(
                    prompt="Say 'test successful' if you can read this.",
                    client=client,
                    model=client_model,
                    system_message="You are a helpful assistant.",
                    print_debug=False
                )
                if "test successful" in response.lower():
                    working_models.append(model)
                    print(f"✅ {model}: Connected")
                else:
                    print(f"⚠️ {model}: Connected but unexpected response")
                    working_models.append(model)  # Still working
            except Exception as e:
                print(f"❌ {model}: {str(e)}")
        
        if working_models:
            print(f"✅ {len(working_models)}/{len(test_models)} models working")
            return True
        else:
            print("❌ No models working - check API keys and connectivity")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def dry_run_test(ideas_file="ai_scientist/ideas/i_cant_believe_its_not_better.json", idea_idx=0):
    """Dry run test - validate everything without running experiments"""
    print(f"\n🏃 Dry Run Test (No Experiments)")
    print("-" * 40)
    
    try:
        # Simulate the launch script setup without running experiments
        import argparse
        from ai_scientist.treesearch.bfts_utils import idea_to_markdown, edit_bfts_config_file
        
        # Load ideas
        with open(ideas_file, "r") as f:
            ideas = json.load(f)
        idea = ideas[idea_idx]
        
        # Create test directory
        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        idea_dir = f"test_experiments/{date}_{idea['Name']}_attempt_test"
        os.makedirs(idea_dir, exist_ok=True)
        
        # Create idea files
        idea_path_md = os.path.join(idea_dir, "idea.md")
        idea_path_json = os.path.join(idea_dir, "idea.json")
        
        idea_to_markdown(idea, idea_path_md, None)
        with open(idea_path_json, "w") as f:
            json.dump(idea, f, indent=4)
        
        # Create config
        config_path = edit_bfts_config_file(
            "test_experiment_config.yaml",
            idea_dir,
            idea_path_json
        )
        
        print("✅ Dry run successful - all setup steps completed")
        print(f"   Test directory: {idea_dir}")
        print("   Ready for actual experiment")
        
        # Cleanup test directory
        shutil.rmtree(idea_dir)
        return True
        
    except Exception as e:
        print(f"❌ Dry run failed: {e}")
        # Cleanup on error
        if 'idea_dir' in locals() and os.path.exists(idea_dir):
            shutil.rmtree(idea_dir)
        return False

def run_ultra_fast_experiment_test(ideas_file="ai_scientist/ideas/i_cant_believe_its_not_better.json", idea_idx=0):
    """Run an ultra-fast experiment to test basic pipeline functionality"""
    print(f"\n⚡ Running Ultra-Fast Experiment Test")
    print("-" * 40)
    print("🚀 Starting ultra-fast experiment (2-min timeout per stage)...")

    # Construct ultra-fast experiment command
    cmd = [
        "python", "launch_scientist_bfts.py",
        "--load_ideas", ideas_file,
        "--idea_idx", str(idea_idx),
        "--writeup-type", "icbinb",  # Shorter 4-page format
        "--num_cite_rounds", "3",  # Minimal citations
        "--writeup-retries", "1",  # Single retry
        "--attempt_id", "888",
        "--model_writeup", "gpt-4o-2024-11-20",  # Faster than O1
        "--model_citation", "gpt-4o-2024-11-20", 
        "--model_review", "gpt-4o-2024-11-20",
        "--model_agg_plots", "gpt-4o-2024-11-20",
        "--force_cpu"  # Use CPU for ultra-fast testing to avoid GPU setup issues
    ]
    
    # Use ultra-fast config
    import shutil
    shutil.copy("ultra_fast_test_config.yaml", "bfts_config.yaml")
    
    print(f"Command: {' '.join(cmd)}")
    print(f"⏱️ This should complete within 30 minutes...")
    
    try:
        # Run the experiment with real-time output
        print("📊 Starting experiment with real-time logging...")
        print("=" * 60)
        
        # Create log file for this experiment
        log_file = f"ultra_fast_experiment_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        print(f"📝 Logging to: {log_file}")
        
        # Start the process without capturing output initially
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Monitor the process with timeout
        import time
        start_time = time.time()
        timeout_seconds = 1800  # 30 minutes for ultra-fast
        
        output_lines = []
        with open(log_file, 'w') as log:
            log.write(f"Ultra-Fast Experiment Log - Started at {datetime.now()}\n")
            log.write(f"Command: {' '.join(cmd)}\n")
            log.write("=" * 80 + "\n\n")
            
            while True:
                # Check if process has finished
                if process.poll() is not None:
                    # Process finished, get remaining output
                    remaining_output = process.stdout.read()
                    if remaining_output:
                        print(remaining_output, end='')
                        output_lines.append(remaining_output)
                        log.write(remaining_output)
                        log.flush()
                    break
                
                # Check for timeout
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    timeout_msg = f"\n⏰ Timeout reached after {elapsed:.1f} seconds\n"
                    print(timeout_msg)
                    log.write(timeout_msg)
                    log.write("🔪 Terminating process...\n")
                    log.flush()
                    print("🔪 Terminating process...")
                    process.terminate()
                    time.sleep(5)  # Give it time to terminate gracefully
                    if process.poll() is None:
                        print("💀 Force killing process...")
                        log.write("💀 Force killing process...\n")
                        process.kill()
                    raise subprocess.TimeoutExpired(cmd, timeout_seconds)
                
                # Read output line by line
                line = process.stdout.readline()
                if line:
                    print(line, end='')
                    output_lines.append(line)
                    log.write(line)
                    
                    # Show progress indicators
                    if "Stage" in line or "Experiment" in line or "Writing" in line or "Plotting" in line:
                        elapsed_min = elapsed / 60
                        progress_msg = f"  ⏱️ [{elapsed_min:.1f}min elapsed]\n"
                        print(progress_msg, end='')
                        log.write(progress_msg)
                    
                    log.flush()  # Ensure we write to disk regularly
                
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
        
        # Create a result-like object for compatibility
        class Result:
            def __init__(self, returncode, stdout):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = ""
        
        result = Result(process.returncode, ''.join(output_lines))
        
        if result.returncode == 0:
            print("✅ Ultra-fast experiment completed successfully!")
            print("🎉 Basic pipeline functionality verified")
            return True
        else:
            print(f"❌ Ultra-fast experiment failed with return code: {result.returncode}")
            return False
    
    except subprocess.TimeoutExpired:
        print("❌ Ultra-fast experiment timed out after 30 minutes")
        print(f"📄 Log file saved: {log_file}")
        
        # Show last few lines of the log to help debug
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    print("\n🔍 Last 10 lines from log:")
                    print("-" * 50)
                    for line in lines[-10:]:
                        print(line.rstrip())
                    print("-" * 50)
        except Exception as e:
            print(f"⚠️ Could not read log file: {e}")
        
        print("🔍 Check the full log file to see where the experiment got stuck")
        return False
    except Exception as e:
        print(f"❌ Ultra-fast experiment failed with error: {str(e)}")
        return False
    finally:
        # Restore original config
        try:
            shutil.copy("test_experiment_config.yaml", "bfts_config.yaml")
        except:
            pass


def run_minimal_experiment_test(ideas_file="ai_scientist/ideas/i_cant_believe_its_not_better.json", idea_idx=0, timeout_minutes=240):
    """Run a minimal experiment to test the full pipeline"""
    print(f"\n🧪 Running Minimal Experiment Test")
    print("-" * 40)
    print("🚀 Starting minimal experiment with GPT-5 for all models...")
    
    # Construct minimal experiment command
    cmd = [
        "python", "launch_scientist_bfts.py",
        "--load_ideas", ideas_file,
        "--idea_idx", str(idea_idx),
        "--writeup-type", "icbinb",  # Shorter 4-page format
        "--num_cite_rounds", "5",  # Reduced citations
        "--writeup-retries", "1",  # Single retry
        "--attempt_id", "999",
        "--model_writeup", "gpt-5",  # Use GPT-5 for paper writing
        "--model_citation", "gpt-5",  # Use GPT-5 for citation gathering
        "--model_review", "gpt-5",  # Use GPT-5 for review
        "--model_agg_plots", "gpt-5"  # Use GPT-5 for plot aggregation
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print(f"⏱️ This should complete within {timeout_minutes} minutes...")
    
    try:
        # Run the experiment with real-time output
        print("📊 Starting experiment with real-time logging...")
        print("=" * 60)
        
        # Create log file for this experiment
        log_file = f"minimal_experiment_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        print(f"📝 Logging to: {log_file}")
        
        # Start the process without capturing output initially
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Monitor the process with timeout
        import time
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        output_lines = []
        with open(log_file, 'w') as log:
            log.write(f"Minimal Experiment Log - Started at {datetime.now()}\n")
            log.write(f"Command: {' '.join(cmd)}\n")
            log.write("=" * 80 + "\n\n")
            
            while True:
                # Check if process has finished
                if process.poll() is not None:
                    # Process finished, get remaining output
                    remaining_output = process.stdout.read()
                    if remaining_output:
                        print(remaining_output, end='')
                        output_lines.append(remaining_output)
                        log.write(remaining_output)
                        log.flush()
                    break
                
                # Check for timeout
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    timeout_msg = f"\n⏰ Timeout reached after {elapsed:.1f} seconds\n"
                    print(timeout_msg)
                    log.write(timeout_msg)
                    log.write("🔪 Terminating process...\n")
                    log.flush()
                    print("🔪 Terminating process...")
                    process.terminate()
                    time.sleep(5)  # Give it time to terminate gracefully
                    if process.poll() is None:
                        print("💀 Force killing process...")
                        log.write("💀 Force killing process...\n")
                        process.kill()
                    raise subprocess.TimeoutExpired(cmd, timeout_seconds)
                
                # Read output line by line
                line = process.stdout.readline()
                if line:
                    print(line, end='')
                    output_lines.append(line)
                    log.write(line)
                    
                    # Show progress indicators
                    if "Stage" in line or "Experiment" in line or "Writing" in line or "Plotting" in line:
                        elapsed_min = elapsed / 60
                        progress_msg = f"  ⏱️ [{elapsed_min:.1f}min elapsed]\n"
                        print(progress_msg, end='')
                        log.write(progress_msg)
                    
                    log.flush()  # Ensure we write to disk regularly
                
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
        
        # Create a result-like object for compatibility
        class Result:
            def __init__(self, returncode, stdout):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = ""
        
        result = Result(process.returncode, ''.join(output_lines))
        
        if result.returncode == 0:
            print("✅ Minimal experiment completed successfully!")
            print("🎉 Your setup is working perfectly!")
            return True
        else:
            print(f"❌ Experiment failed with return code {result.returncode}")
            if result.stderr:
                print("STDERR:", result.stderr)
            if result.stdout:
                print("STDOUT:", result.stdout)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Experiment timed out after 30 minutes")
        print(f"📄 Log file saved: {log_file}")
        
        # Show last few lines of the log to help debug
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    print("\n🔍 Last 10 lines from log:")
                    print("-" * 50)
                    for line in lines[-10:]:
                        print(line.rstrip())
                    print("-" * 50)
        except Exception as e:
            print(f"⚠️ Could not read log file: {e}")
        
        print("🔍 Check the full log file to see where the experiment got stuck")
        return False
    except Exception as e:
        print(f"❌ Error running experiment: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 AI Scientist Experiment Testing Suite")
    print("=" * 50)
    
    # Parse arguments properly
    parser = argparse.ArgumentParser(description="Test AI Scientist experiment setup")
    parser.add_argument("--minimal", action="store_true", help="Run minimal experiment test")
    parser.add_argument("--ultra-fast", action="store_true", help="Run ultra-fast test (2-minute timeout per stage)")
    parser.add_argument("ideas_file", nargs="?", default="ai_scientist/ideas/i_cant_believe_its_not_better.json", help="Path to ideas JSON file")
    parser.add_argument("idea_idx", nargs="?", type=int, default=0, help="Index of idea to test")
    
    args = parser.parse_args()
    
    ideas_file = args.ideas_file
    idea_idx = args.idea_idx
    minimal_test = args.minimal
    ultra_fast_test = args.ultra_fast
    
    print(f"🎯 Testing with: {ideas_file}, idea index: {idea_idx}")
    if ultra_fast_test:
        print("⚡ Running ultra-fast experiment test")
        return run_ultra_fast_experiment_test(ideas_file, idea_idx)
    elif minimal_test:
        print("🚀 Running minimal experiment test")
        return run_minimal_experiment_test(ideas_file, idea_idx)
    
    # Run tests
    tests = [
        ("Basic Setup", test_basic_setup),
        ("Idea Loading", lambda: test_idea_loading(ideas_file, idea_idx)),
        ("Config Creation", lambda: test_config_creation(ideas_file, idea_idx)),
        ("LLM Connectivity", test_llm_connectivity),
        ("Dry Run", lambda: dry_run_test(ideas_file, idea_idx)),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your experiment should run successfully.")
        print("\nNext steps:")
        print("1. Run full experiment:")
        print(f"   python launch_scientist_bfts.py --load_ideas {ideas_file} --idea_idx {idea_idx}")
        print("2. Or run minimal test experiment:")
        print(f"   python test_experiment.py --minimal {ideas_file} {idea_idx}")
        print("3. Or run ultra-fast test experiment:")
        print(f"   python test_experiment.py --ultra-fast {ideas_file} {idea_idx}")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Fix these issues before running experiments.")
        return 1
    
    # Optional minimal experiment
    if minimal_test:
        print("\n" + "=" * 50)
        run_minimal_experiment_test(ideas_file, idea_idx)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 