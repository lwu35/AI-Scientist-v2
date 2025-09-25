# AI Scientist v2 - Enhanced Setup Guide

This repository contains enhanced AI Scientist v2 with significant improvements and bug fixes.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- conda (recommended)
- Git
- GPU (optional but recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/lwu35/AI-Scientist-v2.git
cd AI-Scientist-v2
```

### 2. Create Conda Environment

```bash
conda create -n ai_scientist python=3.11
conda activate ai_scientist
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

```bash
export AI_SCIENTIST_ROOT=$(pwd)
```

Add your API keys:

```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"  # optional
export SEMANTIC_SCHOLAR_API_KEY="your-semantic-scholar-key"  # optional but recommended
```

## 🧪 Testing Your Setup

### Quick Test

```bash
python test_experiment.py --minimal ai_scientist/ideas/i_cant_believe_its_not_better.json 0
```

### Full Test Suite

```bash
python test_experiment.py ai_scientist/ideas/i_cant_believe_its_not_better.json 0
```

## 🔧 Enhanced Features

This fork includes several improvements over the original:

### ✅ Fixed Issues

- **GPT-5/GPT-5-mini Support**: Proper `max_completion_tokens` and `temperature=1` handling
- **Summarization Crash**: Fixed `ValueError: too many values to unpack` in log aggregation
- **Process Cleanup**: Added `psutil` dependency for proper process management
- **Bibliography References**: Automatic LaTeX bibliography reference fixing

### 🚀 New Tools

- **`test_experiment.py`**: Comprehensive testing framework with real-time logging
- **`cleanup_experiment.py`**: Smart experiment cleanup with citation cache management
- **`resume_current_experiment.py`**: Resume crashed experiments from writeup stage
- **`test_experiment_config.yaml`**: Minimal configuration for fast testing

### 📊 Enhanced Monitoring

- Real-time experiment progress logging
- Detailed error reporting and debugging
- Configurable timeouts and retries
- Comprehensive log files for troubleshooting

## 🎯 Usage Examples

### Run a Full Experiment

```bash
python launch_scientist_bfts.py \
    --load_ideas ai_scientist/ideas/i_cant_believe_its_not_better.json \
    --idea_idx 0 \
    --writeup-type icbinb \
    --model_writeup gpt-4o-2024-11-20 \
    --model_citation gpt-4o-2024-11-20 \
    --model_review gpt-4o-2024-11-20
```

### Clean Up After Experiment

```bash
python cleanup_experiment.py experiments/2025-01-01_12-00-00_my_experiment_attempt_0
```

### Resume Crashed Experiment

```bash
python resume_current_experiment.py
```

## 🔍 Troubleshooting

### Common Issues

1. **Missing psutil**:

   ```bash
   pip install psutil
   ```

2. **GPT-5 API Errors**: This fork handles GPT-5 parameter requirements automatically

3. **Experiment Timeouts**: Use `test_experiment.py` with `--minimal` flag for quick testing

4. **Citation Issues**: The fork automatically fixes LaTeX bibliography references

### Getting Help

1. Check the comprehensive logs in `minimal_experiment_log_*.txt`
2. Use the test framework to isolate issues
3. Review the detailed error messages and debugging output

## 📚 Documentation

- **`launch_scientist_bfts_overview.md`**: Comprehensive system documentation
- **`README.md`**: Original project documentation
- **Test logs**: Real-time experiment monitoring and debugging

## 🤝 Contributing

This fork welcomes contributions! Key areas for improvement:

- Additional model support
- Enhanced error handling
- Performance optimizations
- Documentation improvements

## 📄 License

Same as original project - see `LICENSE` file.
