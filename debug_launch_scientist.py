#!/usr/bin/env python3
"""
Debug Launch Scientist GPU Allocation Issues

This script runs launch_scientist_bfts.py with detailed error capture
to diagnose why the GPU allocation tests are failing.
"""

import subprocess
import sys

def debug_launch_scientist():
    """Debug launch_scientist_bfts.py execution with detailed error capture"""
    
    print("🔍 Debugging Launch Scientist GPU Allocation Issues")
    print("=" * 60)
    
    # Test command that failed in the GPU allocation test
    cmd = [
        "python", "launch_scientist_bfts.py",
        "--load_ideas", "ai_scientist/ideas/i_cant_believe_its_not_better.json",
        "--idea_idx", "0",
        "--writeup-type", "icbinb",
        "--skip_writeup",
        "--skip_review", 
        "--attempt_id", "999",
        "--force_cpu"
    ]
    
    print(f"🧪 Running command:")
    print(f"   {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        # Run with detailed output capture
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Capture output line by line
        output_lines = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.rstrip()
                print(line)
                output_lines.append(line)
        
        # Wait for process to complete
        return_code = process.wait()
        
        print("-" * 60)
        print(f"🎯 Process completed with return code: {return_code}")
        
        if return_code != 0:
            print("\n❌ FAILURE ANALYSIS:")
            print("-" * 40)
            
            # Look for common error patterns
            error_patterns = [
                ("ImportError", "Import/dependency issue"),
                ("FileNotFoundError", "Missing file"),
                ("ModuleNotFoundError", "Missing Python module"),
                ("AttributeError", "Code compatibility issue"),
                ("ValueError", "Invalid argument or configuration"),
                ("TypeError", "Type mismatch"),
                ("KeyError", "Missing configuration key"),
                ("Traceback", "Python exception occurred")
            ]
            
            found_errors = []
            for line in output_lines:
                for pattern, description in error_patterns:
                    if pattern in line:
                        found_errors.append(f"  • {description}: {line}")
                        break
            
            if found_errors:
                print("Detected error patterns:")
                for error in found_errors[:5]:  # Show first 5 errors
                    print(error)
            else:
                print("No obvious error patterns detected in output.")
                print("Last 10 lines of output:")
                for line in output_lines[-10:]:
                    print(f"  {line}")
        else:
            print("✅ Process completed successfully!")
            
        return return_code == 0
        
    except Exception as e:
        print(f"❌ Failed to run debug command: {e}")
        return False

if __name__ == "__main__":
    success = debug_launch_scientist()
    if success:
        print("\n🎉 Launch scientist is working correctly!")
    else:
        print("\n⚠️  Launch scientist has issues that need to be addressed.")
    
    sys.exit(0 if success else 1) 