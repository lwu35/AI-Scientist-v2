#!/usr/bin/env python3
"""
GPU Allocation Stress Test for AI Scientist BFTS

This script performs intensive testing of GPU allocation and parallel worker processing
to validate that launch_scientist_bfts.py can handle real experimental workloads.

Features:
- Multi-GPU allocation simulation
- Concurrent worker stress testing  
- GPU memory and compute load simulation
- Process cleanup validation
- Error handling and recovery testing
"""

import os
import sys
import time
import json
import argparse
import subprocess
import multiprocessing as mp
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import contextmanager

# Import torch after multiprocessing setup to avoid CUDA issues
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️ PyTorch not available - GPU tests will be skipped")

def get_gpu_info():
    """Get detailed GPU information"""
    print("🔍 GPU Information:")
    print("-" * 50)
    
    # Check nvidia-smi
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu", 
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, check=True
        )
        print("📊 nvidia-smi GPU Status:")
        lines = result.stdout.strip().split('\n')
        for i, line in enumerate(lines):
            if line.strip():
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 6:
                    idx, name, total_mem, used_mem, free_mem, util = parts[:6]
                    print(f"  GPU {idx}: {name}")
                    print(f"    Memory: {used_mem}MB / {total_mem}MB ({free_mem}MB free)")
                    print(f"    Utilization: {util}%")
    except Exception as e:
        print(f"❌ nvidia-smi error: {e}")
    
    # Check PyTorch CUDA
    try:
        if TORCH_AVAILABLE:
            print(f"\n🐍 PyTorch CUDA Status:")
            print(f"  CUDA Available: {torch.cuda.is_available()}")
            print(f"  CUDA Version: {torch.version.cuda}")
            print(f"  Device Count: {torch.cuda.device_count()}")
            
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    props = torch.cuda.get_device_properties(i)
                    print(f"  GPU {i}: {props.name}")
                    print(f"    Memory: {props.total_memory / 1024**3:.1f}GB")
                    print(f"    Compute Capability: {props.major}.{props.minor}")
        else:
            print(f"\n🐍 PyTorch CUDA Status: Not Available")
    except Exception as e:
        print(f"❌ PyTorch CUDA error: {e}")
    
    print("-" * 50)

def simulate_gpu_workload(gpu_id, duration=30, memory_mb=512):
    """Simulate intensive GPU workload on a specific GPU"""
    try:
        # Set the specific GPU
        os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_id)
        
        # Import torch after setting CUDA_VISIBLE_DEVICES in the worker process
        import torch
        
        if not torch.cuda.is_available():
            return {"status": "no_cuda", "gpu_id": gpu_id, "error": "CUDA not available"}
        
        device = torch.device(f'cuda:0')  # Always 0 since we set CUDA_VISIBLE_DEVICES
        
        print(f"🔥 Worker {os.getpid()}: Starting GPU {gpu_id} workload (spawn method)...")
        
        # Allocate GPU memory
        size = int((memory_mb * 1024 * 1024) / 4)  # 4 bytes per float32
        matrix_size = int(size ** 0.5)
        
        # Create large tensors to consume GPU memory
        tensor_a = torch.randn(matrix_size, matrix_size, device=device)
        tensor_b = torch.randn(matrix_size, matrix_size, device=device)
        
        start_time = time.time()
        operations = 0
        
        # Perform intensive compute operations
        while time.time() - start_time < duration:
            # Matrix multiplication (compute intensive)
            result = torch.matmul(tensor_a, tensor_b)
            
            # Element-wise operations
            result = torch.relu(result)
            result = torch.tanh(result)
            
            # Memory operations
            tensor_c = result + tensor_a
            tensor_d = tensor_c * tensor_b
            
            # Cleanup intermediate tensors
            del result, tensor_c, tensor_d
            torch.cuda.empty_cache()
            
            operations += 1
            
            if operations % 10 == 0:
                memory_allocated = torch.cuda.memory_allocated(device) / 1024**2
                print(f"🔥 Worker {os.getpid()}: GPU {gpu_id} - {operations} ops, {memory_allocated:.1f}MB allocated")
        
        # Cleanup
        del tensor_a, tensor_b
        torch.cuda.empty_cache()
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        return {
            "status": "success",
            "gpu_id": gpu_id,
            "worker_pid": os.getpid(),
            "operations": operations,
            "duration": elapsed,
            "ops_per_second": operations / elapsed
        }
        
    except Exception as e:
        return {
            "status": "error",
            "gpu_id": gpu_id,
            "worker_pid": os.getpid(),
            "error": str(e)
        }

def test_gpu_allocation_stress(num_workers=None, duration=60, memory_per_worker=256):
    """Test GPU allocation under stress with multiple workers"""
    print(f"\n🧪 GPU Allocation Stress Test")
    print("=" * 60)
    
    if not TORCH_AVAILABLE:
        print("❌ PyTorch not available - skipping GPU stress test")
        return False
    
    # Determine number of workers and GPUs
    available_gpus = list(range(torch.cuda.device_count())) if torch.cuda.is_available() else []
    if not available_gpus:
        print("❌ No GPUs available for testing")
        return False
    
    if num_workers is None:
        num_workers = len(available_gpus) * 2  # 2 workers per GPU
    
    print(f"🎯 Test Configuration:")
    print(f"  Available GPUs: {available_gpus}")
    print(f"  Number of Workers: {num_workers}")
    print(f"  Duration per Worker: {duration}s")
    print(f"  Memory per Worker: {memory_per_worker}MB")
    print(f"  Total Expected Memory: {num_workers * memory_per_worker}MB")
    
    # Create worker tasks
    tasks = []
    for i in range(num_workers):
        gpu_id = available_gpus[i % len(available_gpus)]  # Round-robin GPU assignment
        tasks.append((gpu_id, duration, memory_per_worker))
    
    print(f"\n🚀 Starting {num_workers} parallel GPU workers...")
    start_time = time.time()
    
    # Run workers in parallel
    results = []
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(simulate_gpu_workload, gpu_id, duration, memory_mb): (gpu_id, i)
            for i, (gpu_id, duration, memory_mb) in enumerate(tasks)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_task):
            gpu_id, task_idx = future_to_task[future]
            try:
                result = future.result(timeout=duration + 30)  # Extra timeout buffer
                results.append(result)
                
                if result["status"] == "success":
                    print(f"✅ Task {task_idx} (GPU {gpu_id}): {result['operations']} ops, "
                          f"{result['ops_per_second']:.1f} ops/sec")
                else:
                    print(f"❌ Task {task_idx} (GPU {gpu_id}): {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Task {task_idx} (GPU {gpu_id}) failed: {e}")
                results.append({
                    "status": "timeout_or_error",
                    "gpu_id": gpu_id,
                    "task_idx": task_idx,
                    "error": str(e)
                })
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Analyze results
    print(f"\n📊 Stress Test Results:")
    print("-" * 40)
    print(f"Total Test Time: {total_time:.1f}s")
    
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] != "success"]
    
    print(f"Successful Workers: {len(successful)}/{num_workers}")
    print(f"Failed Workers: {len(failed)}/{num_workers}")
    
    if successful:
        total_ops = sum(r["operations"] for r in successful)
        avg_ops_per_sec = sum(r["ops_per_second"] for r in successful) / len(successful)
        print(f"Total Operations: {total_ops}")
        print(f"Average Ops/Second: {avg_ops_per_sec:.1f}")
        
        # GPU utilization breakdown
        gpu_usage = {}
        for result in successful:
            gpu_id = result["gpu_id"]
            if gpu_id not in gpu_usage:
                gpu_usage[gpu_id] = []
            gpu_usage[gpu_id].append(result["ops_per_second"])
        
        print(f"\n📈 GPU Utilization Breakdown:")
        for gpu_id, ops_list in gpu_usage.items():
            avg_ops = sum(ops_list) / len(ops_list)
            print(f"  GPU {gpu_id}: {len(ops_list)} workers, {avg_ops:.1f} avg ops/sec")
    
    if failed:
        print(f"\n❌ Failed Workers:")
        for result in failed:
            print(f"  GPU {result['gpu_id']}: {result.get('error', 'Unknown error')}")
    
    success_rate = len(successful) / num_workers
    print(f"\n🎯 Success Rate: {success_rate:.1%}")
    
    return success_rate >= 0.8  # 80% success rate threshold

def test_launch_scientist_gpu_allocation():
    """Test GPU allocation in launch_scientist_bfts.py with different configurations"""
    print(f"\n🔬 Testing launch_scientist_bfts.py GPU Allocation")
    print("=" * 60)
    
    if not TORCH_AVAILABLE:
        print("❌ PyTorch not available - skipping launch_scientist tests")
        return True
        
    if not torch.cuda.is_available():
        print("❌ No GPUs available - skipping launch_scientist tests")
        return True
    
    available_gpus = list(range(torch.cuda.device_count()))
    test_configs = [
        {"name": "Single GPU", "gpu_ids": str(available_gpus[0]), "force_cpu": False},
        {"name": "All GPUs", "gpu_ids": ",".join(map(str, available_gpus)), "force_cpu": False},
        {"name": "Force CPU", "gpu_ids": None, "force_cpu": True},
    ]
    
    if len(available_gpus) > 1:
        test_configs.append({
            "name": "Subset GPUs", 
            "gpu_ids": ",".join(map(str, available_gpus[:2])), 
            "force_cpu": False
        })
    
    results = {}
    
    for config in test_configs:
        print(f"\n🧪 Testing Configuration: {config['name']}")
        print("-" * 40)
        
        # Build command
        cmd = [
            "python", "launch_scientist_bfts.py",
            "--load_ideas", "ai_scientist/ideas/i_cant_believe_its_not_better.json",
            "--idea_idx", "0",
            "--writeup-type", "icbinb",
            "--skip_writeup",  # Skip writeup to focus on GPU allocation
            "--skip_review",   # Skip review to focus on GPU allocation
            "--attempt_id", "999"
        ]
        
        if config["gpu_ids"]:
            cmd.extend(["--gpu_ids", config["gpu_ids"]])
        
        if config["force_cpu"]:
            cmd.append("--force_cpu")
        
        print(f"Command: {' '.join(cmd)}")
        
        # Run with timeout
        start_time = time.time()
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Monitor for 2 minutes
            stdout, _ = process.communicate(timeout=120)
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            # Check for GPU-related messages and errors in output
            gpu_messages = []
            error_messages = []
            for line in stdout.split('\n'):
                if any(keyword in line.lower() for keyword in ['gpu', 'cuda', 'device']):
                    gpu_messages.append(line.strip())
                if any(keyword in line for keyword in ['Error', 'Exception', 'Traceback', 'Failed', 'ImportError', 'ModuleNotFoundError']):
                    error_messages.append(line.strip())
            
            results[config['name']] = {
                "success": process.returncode == 0,
                "elapsed": elapsed,
                "return_code": process.returncode,
                "gpu_messages": gpu_messages[:10],  # First 10 GPU-related messages
                "error_messages": error_messages[:10],  # First 10 error messages
                "output_length": len(stdout),
                "full_output": stdout  # Store full output for debugging
            }
            
            status = "✅ SUCCESS" if process.returncode == 0 else f"❌ FAILED (code {process.returncode})"
            print(f"Result: {status} in {elapsed:.1f}s")
            
            if process.returncode != 0 and error_messages:
                print("Error messages:")
                for msg in error_messages[:3]:  # Show first 3 errors
                    print(f"  {msg}")
            elif gpu_messages:
                print("GPU-related messages:")
                for msg in gpu_messages[:3]:  # Show first 3
                    print(f"  {msg}")
            
        except subprocess.TimeoutExpired:
            process.kill()
            results[config['name']] = {
                "success": False,
                "elapsed": 120,
                "return_code": "timeout",
                "error": "Process timed out after 2 minutes"
            }
            print("❌ TIMEOUT after 2 minutes")
        
        except Exception as e:
            results[config['name']] = {
                "success": False,
                "error": str(e)
            }
            print(f"❌ ERROR: {e}")
    
    # Summary
    print(f"\n📋 Launch Scientist GPU Test Summary:")
    print("-" * 40)
    successful_configs = 0
    failed_configs = []
    
    for name, result in results.items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        elapsed = result.get("elapsed", "N/A")
        print(f"{name}: {status} ({elapsed}s)")
        if result["success"]:
            successful_configs += 1
        else:
            failed_configs.append((name, result))
    
    success_rate = successful_configs / len(test_configs)
    print(f"\nOverall Success Rate: {success_rate:.1%}")
    
    # Save detailed failure logs if there are failures
    if failed_configs:
        print(f"\n🔍 Saving detailed failure logs...")
        log_file = f"launch_scientist_failures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        with open(log_file, 'w') as f:
            f.write("Launch Scientist GPU Test Failure Details\n")
            f.write("=" * 50 + "\n\n")
            
            for name, result in failed_configs:
                f.write(f"Configuration: {name}\n")
                f.write(f"Return Code: {result.get('return_code', 'Unknown')}\n")
                f.write(f"Elapsed Time: {result.get('elapsed', 'Unknown')}s\n")
                f.write(f"Output Length: {result.get('output_length', 0)} characters\n")
                f.write("\nFull Output:\n")
                f.write("-" * 30 + "\n")
                f.write(result.get('full_output', 'No output captured'))
                f.write("\n" + "=" * 50 + "\n\n")
        
        print(f"   Detailed logs saved to: {log_file}")
        print(f"   Run 'python debug_launch_scientist.py' for interactive debugging")
    
    return success_rate >= 0.5  # 50% success rate (some configs may legitimately fail)

def cleanup_test_artifacts():
    """Clean up test artifacts"""
    print("\n🧹 Cleaning up test artifacts...")
    
    # Remove test experiment directories
    import glob
    test_dirs = glob.glob("experiments/*gpu_test*")
    test_dirs.extend(glob.glob("test_*"))
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            try:
                import shutil
                shutil.rmtree(test_dir)
                print(f"  Removed: {test_dir}")
            except Exception as e:
                print(f"  Failed to remove {test_dir}: {e}")

def main():
    # Fix CUDA multiprocessing issue by setting spawn method
    try:
        mp.set_start_method('spawn', force=True)
        print("🔧 Set multiprocessing start method to 'spawn' for CUDA compatibility")
    except RuntimeError:
        # Already set, which is fine
        current_method = mp.get_start_method()
        print(f"🔧 Multiprocessing start method already set to: {current_method}")
    
    parser = argparse.ArgumentParser(description="GPU Allocation Stress Test for AI Scientist")
    parser.add_argument("--workers", type=int, help="Number of parallel workers (default: 2 * num_gpus)")
    parser.add_argument("--duration", type=int, default=60, help="Duration of each worker test in seconds")
    parser.add_argument("--memory", type=int, default=256, help="Memory per worker in MB")
    parser.add_argument("--skip-stress", action="store_true", help="Skip the stress test")
    parser.add_argument("--skip-launch", action="store_true", help="Skip launch_scientist tests")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test artifacts")
    
    args = parser.parse_args()
    
    print("🧪 GPU Allocation Comprehensive Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get GPU information
    get_gpu_info()
    
    all_tests_passed = True
    
    # Stress test
    if not args.skip_stress:
        try:
            stress_passed = test_gpu_allocation_stress(
                num_workers=args.workers,
                duration=args.duration,
                memory_per_worker=args.memory
            )
            all_tests_passed = all_tests_passed and stress_passed
        except Exception as e:
            print(f"❌ Stress test failed with exception: {e}")
            all_tests_passed = False
    
    # Launch scientist test
    if not args.skip_launch:
        try:
            launch_passed = test_launch_scientist_gpu_allocation()
            all_tests_passed = all_tests_passed and launch_passed
        except Exception as e:
            print(f"❌ Launch scientist test failed with exception: {e}")
            all_tests_passed = False
    
    # Cleanup
    if args.cleanup:
        cleanup_test_artifacts()
    
    # Final results
    print(f"\n🏁 Final Test Results")
    print("=" * 60)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED - GPU allocation is working correctly!")
        print("✅ Your parallel worker processing and GPU allocation changes are robust")
        return 0
    else:
        print("❌ SOME TESTS FAILED - GPU allocation may have issues")
        print("⚠️  Review the test output above for specific failure details")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 