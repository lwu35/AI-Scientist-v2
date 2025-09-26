# GPU Allocation Stress Test Guide

This guide explains how to use `test_gpu_allocation.py` to validate your parallel worker processing and GPU allocation changes in `launch_scientist_bfts.py`.

## Overview

The test script performs two main types of testing:

1. **GPU Allocation Stress Test** - Simulates intensive parallel GPU workloads
2. **Launch Scientist Integration Test** - Tests actual `launch_scientist_bfts.py` with different GPU configurations

## Quick Start

### Basic Test (Recommended)

```bash
python test_gpu_allocation.py
```

### Quick Stress Test (30 seconds per worker)

```bash
python test_gpu_allocation.py --duration 30 --memory 128
```

### Skip Stress Test, Only Test Launch Scientist

```bash
python test_gpu_allocation.py --skip-stress
```

### Ultra-Intensive Test (High Memory, Long Duration)

```bash
python test_gpu_allocation.py --workers 8 --duration 120 --memory 512
```

## Command Line Options

| Option          | Description                            | Default        |
| --------------- | -------------------------------------- | -------------- |
| `--workers N`   | Number of parallel workers             | `2 * num_gpus` |
| `--duration N`  | Duration of each worker test (seconds) | `60`           |
| `--memory N`    | Memory per worker (MB)                 | `256`          |
| `--skip-stress` | Skip the stress test                   | `False`        |
| `--skip-launch` | Skip launch_scientist tests            | `False`        |
| `--cleanup`     | Clean up test artifacts                | `False`        |

## Test Scenarios

### Scenario 1: Basic Validation

**Purpose**: Quick validation that GPU allocation is working

```bash
python test_gpu_allocation.py --duration 30 --memory 128
```

**Expected**: 80%+ success rate, no GPU allocation conflicts

### Scenario 2: Memory Stress Test

**Purpose**: Test GPU memory allocation under pressure

```bash
python test_gpu_allocation.py --workers 4 --memory 1024 --duration 60
```

**Expected**: Should handle high memory usage without crashes

### Scenario 3: Multi-Worker Intensive

**Purpose**: Simulate real experimental workload with many parallel workers

```bash
python test_gpu_allocation.py --workers 12 --duration 90 --memory 256
```

**Expected**: Proper round-robin GPU assignment, stable performance

### Scenario 4: Launch Scientist Only

**Purpose**: Test actual integration with your changes

```bash
python test_gpu_allocation.py --skip-stress
```

**Expected**: Different GPU configurations should work correctly

## Understanding Results

### Stress Test Results

- **Success Rate**: Should be ≥80% for robust GPU allocation
- **Ops/Second**: Higher is better, indicates efficient GPU utilization
- **GPU Utilization Breakdown**: Should show balanced load across GPUs

### Launch Scientist Results

- **Single GPU**: Tests specific GPU assignment
- **All GPUs**: Tests multi-GPU coordination
- **Force CPU**: Tests CPU fallback
- **Subset GPUs**: Tests partial GPU allocation

## Common Issues and Solutions

### Issue: Low Success Rate (<80%)

**Possible Causes**:

- GPU memory conflicts
- CUDA context issues
- Process cleanup problems

**Solutions**:

- Reduce `--memory` parameter
- Check for zombie processes: `ps aux | grep python`
- Restart and try with fewer workers

### Issue: "CUDA out of memory"

**Possible Causes**:

- Too many workers or too much memory per worker
- Previous processes didn't clean up properly

**Solutions**:

```bash
# Clear GPU memory
nvidia-smi --gpu-reset
# Or reduce memory usage
python test_gpu_allocation.py --memory 128 --workers 2
```

### Issue: Launch Scientist Tests Timeout

**Possible Causes**:

- Slow initialization
- GPU allocation deadlock
- Configuration issues

**Solutions**:

- Check GPU setup: `nvidia-smi`
- Verify CUDA environment: `python -c "import torch; print(torch.cuda.is_available())"`
- Run with verbose output to see where it hangs

## Interpreting GPU Messages

The test captures GPU-related messages from `launch_scientist_bfts.py`. Look for:

### Good Signs ✅

```
🎮 Using GPUs: [0, 1, 2, 3]
🔍 GPU Setup Validation:
CUDA_VISIBLE_DEVICES: 0,1,2,3
✅ GPU validation successful
```

### Warning Signs ⚠️

```
⚠️ No GPUs detected - falling back to CPU mode
ValueError: Cannot close a process while it is still running
CUDA out of memory
```

### Critical Issues ❌

```
Failed to allocate GPU resources
Process cleanup failed
GPU allocation deadlock detected
```

## Performance Benchmarks

### Expected Performance (per GPU)

- **Operations/Second**: 50-200 (depends on GPU model)
- **Memory Allocation**: Should handle 256MB+ per worker
- **Worker Scaling**: Linear scaling up to GPU memory limits

### Multi-GPU Scaling

- **2 GPUs**: ~1.8x performance of single GPU
- **4 GPUs**: ~3.5x performance of single GPU
- **8 GPUs**: ~6-7x performance (may hit other bottlenecks)

## Advanced Usage

### Custom Test Configuration

Create a custom test by modifying the script or using environment variables:

```bash
# Test with specific CUDA devices
CUDA_VISIBLE_DEVICES=0,2 python test_gpu_allocation.py --workers 4

# Test with reduced GPU memory
python test_gpu_allocation.py --memory 64 --workers 16
```

### Integration with CI/CD

```bash
# Non-interactive test suitable for CI
python test_gpu_allocation.py --duration 15 --memory 64 --cleanup
if [ $? -eq 0 ]; then
    echo "GPU allocation tests passed"
else
    echo "GPU allocation tests failed"
    exit 1
fi
```

## Troubleshooting

### Debug Mode

Add debug prints to see detailed GPU allocation:

```python
# Add to launch_scientist_bfts.py for debugging
print(f"DEBUG: Worker {os.getpid()} using GPU {os.environ.get('CUDA_VISIBLE_DEVICES')}")
```

### Monitor GPU Usage During Test

```bash
# In another terminal, monitor GPU usage
watch -n 1 nvidia-smi

# Or log GPU usage
nvidia-smi --query-gpu=timestamp,index,utilization.gpu,memory.used --format=csv -l 1 > gpu_usage.log
```

### Check Process Cleanup

```bash
# Before test
ps aux | grep python | wc -l

# After test (should be similar)
ps aux | grep python | wc -l

# If many processes remain, there may be cleanup issues
```

## Expected Test Duration

| Test Type   | Duration     | Description                  |
| ----------- | ------------ | ---------------------------- |
| Basic       | 2-3 minutes  | Default settings             |
| Quick       | 1-2 minutes  | `--duration 30`              |
| Intensive   | 5-10 minutes | `--workers 8 --duration 120` |
| Launch Only | 3-5 minutes  | `--skip-stress`              |

## Success Criteria

Your GPU allocation implementation is robust if:

1. ✅ **Stress Test**: ≥80% success rate
2. ✅ **Launch Scientist**: ≥50% configurations pass (some may legitimately fail)
3. ✅ **No Memory Leaks**: Process count returns to baseline
4. ✅ **Balanced GPU Usage**: All GPUs show similar utilization
5. ✅ **Clean Shutdown**: No hanging processes or CUDA contexts

## Next Steps

After successful testing:

1. **Run Real Experiments**: Your GPU allocation should handle actual training workloads
2. **Monitor Production**: Watch for similar patterns in real experiments
3. **Scale Testing**: Try with larger models and longer durations
4. **Performance Tuning**: Adjust worker counts based on your specific GPU setup

---

**Note**: This test is designed to be more intensive than typical experimental workloads to ensure robustness under stress conditions.
