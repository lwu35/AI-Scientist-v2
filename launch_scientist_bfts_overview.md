# AI Scientist BFTS Launch Script - Comprehensive Overview

## Table of Contents

- [System Context](#system-context)
- [Architecture & Dependencies](#architecture--dependencies)
- [Configuration System](#configuration-system)
- [Main Execution Pipeline](#main-execution-pipeline)
- [Advanced Features](#advanced-features)
- [Key Design Patterns](#key-design-patterns)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

## System Context

The AI Scientist-v2 is an autonomous scientific research system that generates hypotheses, runs experiments, analyzes data, and writes scientific manuscripts. The `launch_scientist_bfts.py` script serves as the **main orchestrator** for this entire pipeline, coordinating multiple complex subsystems to produce complete research papers from initial ideas.

### Key Capabilities

- **Autonomous Research**: From hypothesis to peer-reviewed paper
- **Multi-Stage Experimentation**: Using Breadth-First Tree Search (BFTS)
- **Automated Writing**: LaTeX paper generation with citations
- **Peer Review**: Automated review using LLMs and Vision-Language Models
- **Resource Management**: GPU allocation and process lifecycle management

## Architecture & Dependencies

### Core System Components

```python
# Experimental System
from ai_scientist.treesearch.perform_experiments_bfts_with_agentmanager import perform_experiments_bfts
from ai_scientist.treesearch.bfts_utils import idea_to_markdown, edit_bfts_config_file

# Paper Generation Pipeline
from ai_scientist.perform_plotting import aggregate_plots
from ai_scientist.perform_writeup import perform_writeup
from ai_scientist.perform_icbinb_writeup import perform_writeup as perform_icbinb_writeup

# Review & Evaluation
from ai_scientist.perform_llm_review import perform_review, load_paper
from ai_scientist.perform_vlm_review import perform_imgs_cap_ref_review
```

### System Integration

The script integrates several sophisticated subsystems:

1. **BFTS (Breadth-First Tree Search)** - Multi-agent experimental exploration
2. **Multi-format Paper Generation** - Normal (8-page) vs ICBINB (4-page) formats
3. **Automated Peer Review** - Using both text and vision language models
4. **Citation Management** - Semantic search and bibliography generation
5. **Resource Management** - GPU allocation and process cleanup

## Configuration System

### Command-Line Arguments

| Argument            | Default                                      | Description                                          |
| ------------------- | -------------------------------------------- | ---------------------------------------------------- |
| `--writeup-type`    | `"icbinb"`                                   | Paper format: "normal" (8-page) or "icbinb" (4-page) |
| `--load_ideas`      | `"ideas/i_cant_believe_its_not_better.json"` | Path to research ideas JSON file                     |
| `--idea_idx`        | `0`                                          | Index of idea to execute from the JSON file          |
| `--load_code`       | `False`                                      | Load Python code file with same name as ideas file   |
| `--add_dataset_ref` | `False`                                      | Add HuggingFace dataset reference                    |
| `--writeup-retries` | `3`                                          | Number of writeup attempts                           |
| `--attempt_id`      | `0`                                          | Attempt ID for parallel runs                         |

### Model Configuration

| Stage               | Default Model             | Purpose                         |
| ------------------- | ------------------------- | ------------------------------- |
| `--model_agg_plots` | `"o3-mini-2025-01-31"`    | Plot generation and aggregation |
| `--model_writeup`   | `"o1-preview-2024-09-12"` | Scientific paper writing        |
| `--model_citation`  | `"gpt-4o-2024-11-20"`     | Citation gathering              |
| `--model_review`    | `"gpt-4o-2024-11-20"`     | Automated paper review          |

### BFTS Configuration (`bfts_config.yaml`)

```yaml
# Agent Configuration
agent:
  type: parallel
  num_workers: 4 # Parallel exploration paths
  steps: 5 # Maximum nodes to explore

  # Stage-specific iterations
  stages:
    stage1_max_iters: 20 # Initial implementation
    stage2_max_iters: 12 # Baseline tuning
    stage3_max_iters: 12 # Creative research
    stage4_max_iters: 18 # Ablation studies

# Search Parameters
search:
  max_debug_depth: 3 # Debug attempts per failing node
  debug_prob: 0.5 # Probability of debugging failures
  num_drafts: 3 # Independent trees to grow

# LLM Configuration
code:
  model: claude-3-5-sonnet-20241022
  temp: 1.0
  max_tokens: 12000

feedback:
  model: gpt-4o-2024-11-20
  temp: 0.5
  max_tokens: 8192
```

## Main Execution Pipeline

### Stage 1: Initialization & Setup

```python
# GPU Detection and Resource Allocation
available_gpus = get_available_gpus()
print(f"Using GPUs: {available_gpus}")

# Create Timestamped Experiment Directory
date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
idea_dir = f"experiments/{date}_{idea['Name']}_attempt_{args.attempt_id}"
os.makedirs(idea_dir, exist_ok=True)
```

**Key Operations:**

- Detects available CUDA GPUs
- Creates unique experiment directory with timestamp
- Sets up workspace for all pipeline stages

### Stage 2: Idea Processing

```python
# Load Research Ideas
with open(args.load_ideas, "r") as f:
    ideas = json.load(f)
idea = ideas[args.idea_idx]

# Convert to Markdown Format
idea_to_markdown(ideas[args.idea_idx], idea_path_md, code_path)
```

**Idea Structure:**

```json
{
  "Name": "compositional_regularization_nn",
  "Title": "Enhancing Compositional Generalization in Neural Networks",
  "Short Hypothesis": "Introducing compositional regularization...",
  "Abstract": "Neural networks excel in many tasks but...",
  "Experiments": [
    "Implement the compositional regularization term...",
    "Train models on synthetic datasets like SCAN..."
  ],
  "Risk Factors and Limitations": [
    "The effectiveness may vary across different datasets..."
  ]
}
```

### Stage 3: BFTS Experimental System

```python
# Configure and Launch Tree Search Experiments
idea_config_path = edit_bfts_config_file(config_path, idea_dir, idea_path_json)
perform_experiments_bfts(idea_config_path)
```

**BFTS Process Flow:**

1. **AgentManager Initialization**

   - Creates 4 main experimental stages
   - Sets up parallel worker processes
   - Initializes journals for tracking results

2. **Four-Stage Research Process:**

   - **Stage 1 - Initial Implementation**: Basic working implementation
   - **Stage 2 - Baseline Tuning**: Performance optimization and parameter tuning
   - **Stage 3 - Creative Research**: Novel approaches and experimental variations
   - **Stage 4 - Ablation Studies**: Systematic component analysis

3. **Parallel Tree Search:**

   - Each node represents an experimental state
   - Children nodes are variations/improvements
   - Multiple workers explore different paths simultaneously
   - Best results propagate to subsequent stages

4. **Automatic Debugging:**
   - Failed experiments trigger debugging attempts
   - Up to 3 debug iterations per failing node
   - 50% probability of attempting debug on failures

### Stage 4: Plot Generation

```python
aggregate_plots(base_folder=idea_dir, model=args.model_agg_plots)
```

**Plot Aggregation Process:**

- Analyzes all experimental results from BFTS stages
- Generates up to 12 comprehensive scientific figures
- Creates professional visualizations with proper labeling
- Organizes plots for main paper and appendix inclusion
- Uses existing `.npy` data files for accurate representation

### Stage 5: Paper Writing

```python
# Citation Gathering
citations_text = gather_citations(
    idea_dir,
    num_cite_rounds=args.num_cite_rounds,
    small_model=args.model_citation,
)

# Bibliography Reference Fix (Critical for LaTeX)
if '\\bibliography{iclr2025}' in content:
    content = content.replace('\\bibliography{iclr2025}', '\\bibliography{references}')

# Writeup Generation with Retries
for attempt in range(args.writeup_retries):
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
```

**Paper Generation Features:**

- **Semantic Citation Search**: 20 rounds of literature search by default
- **LaTeX Template Management**: Automatic bibliography reference fixes
- **Multiple Paper Formats**: Normal (8-page) vs ICBINB (4-page) workshop format
- **Retry Mechanism**: Up to 3 attempts if compilation fails
- **Advanced Language Models**: Uses models like o1-preview for high-quality writing

### Stage 6: Automated Review

```python
# Locate Latest Paper PDF
pdf_path = find_pdf_path_for_review(idea_dir)

# Comprehensive Review Process
paper_content = load_paper(pdf_path)
review_text = perform_review(paper_content, client_model, client)
review_img_cap_ref = perform_imgs_cap_ref_review(client, client_model, pdf_path)
```

**Review System Components:**

1. **Text-Based Review:**

   - Analyzes paper content using NeurIPS review criteria
   - Evaluates originality, quality, clarity, significance
   - Provides detailed strengths and weaknesses
   - Generates numerical ratings (1-10 scale)

2. **Visual Review:**

   - Examines figures, captions, and references using vision models
   - Checks for visual clarity and appropriateness
   - Validates figure-text correspondence

3. **Review Output:**
   - Structured JSON format with all evaluation criteria
   - Binary accept/reject recommendation
   - Detailed feedback for potential improvements

## Advanced Features

### Intelligent PDF Processing

```python
def find_pdf_path_for_review(idea_dir):
    """
    Sophisticated PDF selection logic:
    1. Prioritizes reflection PDFs (iterative improvements)
    2. Finds highest numbered reflection (e.g., reflection_3.pdf)
    3. Falls back to final versions if available
    4. Uses any available PDF as last resort
    """
```

### Token Usage Tracking

```python
def save_token_tracker(idea_dir):
    """
    Comprehensive API usage monitoring:
    - Tracks all LLM API calls across pipeline stages
    - Records token usage per model and operation
    - Saves detailed interaction logs for cost analysis
    - Enables budget management for large experiments
    """
```

### Process Management & Cleanup

```python
# Comprehensive Cleanup System
import psutil
import signal

# Graceful Process Termination
for child in children:
    child.send_signal(signal.SIGTERM)

# Force Termination if Necessary
gone, alive = psutil.wait_procs(children, timeout=3)
for process in alive:
    process.kill()

# Orphaned Process Cleanup
keywords = ["python", "torch", "mp", "bfts", "experiment"]
for proc in psutil.process_iter(["name", "cmdline"]):
    cmdline = " ".join(proc.cmdline()).lower()
    if any(keyword in cmdline for keyword in keywords):
        proc.terminate()
```

**Why Comprehensive Cleanup is Critical:**

- BFTS spawns numerous parallel processes
- GPU processes can become zombie processes
- Prevents resource leaks in long-running experiments
- Ensures clean system state for subsequent runs

## Key Design Patterns

### 1. Error Resilience

- **Multiple Retry Mechanisms**: Writeup generation attempts up to 3 times
- **Graceful Degradation**: System continues if non-critical components fail
- **Comprehensive Logging**: Detailed error tracking for debugging

### 2. Modular Architecture

- **Independent Stages**: Experiments, plotting, writeup, review can run separately
- **Skip Flags**: `--skip_writeup`, `--skip_review` for partial execution
- **Extensible Design**: Easy to add new paper formats or review methods

### 3. Resource Management

- **GPU Detection**: Automatic CUDA device discovery and allocation
- **Token Tracking**: Cost monitoring for LLM API usage
- **Process Lifecycle**: Complete process management from spawn to cleanup

### 4. Configuration-Driven Design

- **YAML Configuration**: Flexible experimental parameter tuning
- **Command-Line Overrides**: Easy customization for different use cases
- **Model Selection**: Per-stage model configuration for optimal performance

## Usage Examples

### Basic Execution

```bash
python launch_scientist_bfts.py \
    --load_ideas ideas/my_research_topic.json \
    --idea_idx 0 \
    --writeup-type icbinb
```

### Advanced Configuration

```bash
python launch_scientist_bfts.py \
    --load_ideas ideas/compositional_learning.json \
    --idea_idx 2 \
    --load_code \
    --writeup-type normal \
    --model_writeup "o1-2024-12-17" \
    --model_review "gpt-4o-2024-11-20" \
    --writeup-retries 5 \
    --num_cite_rounds 30 \
    --attempt_id 1
```

### Parallel Execution

```bash
# Run multiple ideas in parallel
for i in {0..3}; do
    python launch_scientist_bfts.py \
        --load_ideas ideas/batch_experiments.json \
        --idea_idx $i \
        --attempt_id $i &
done
```

## Troubleshooting

### Common Issues

1. **GPU Memory Issues**

   - Reduce `num_workers` in `bfts_config.yaml`
   - Monitor GPU usage with `nvidia-smi`
   - Ensure proper cleanup between runs

2. **LaTeX Compilation Errors**

   - Check bibliography reference fixes are applied
   - Verify all required LaTeX packages are installed
   - Review generated `.tex` files for syntax errors

3. **API Rate Limits**

   - Monitor token usage in `token_tracker.json`
   - Implement delays between API calls if needed
   - Use different models to distribute load

4. **Process Cleanup Issues**
   - Run cleanup script manually if needed
   - Check for orphaned processes with `ps aux | grep python`
   - Restart system if persistent issues occur

### Debug Information

The system generates extensive logs in the experiment directory:

- `logs/`: BFTS execution logs and tree search progress
- `token_tracker.json`: API usage statistics
- `review_text.txt`: Automated review results
- `latex/`: Generated LaTeX files and compilation logs

### Performance Optimization

- **Model Selection**: Use faster models for non-critical stages
- **Parallel Workers**: Adjust based on available GPU memory
- **Citation Rounds**: Reduce for faster execution in development
- **Skip Flags**: Use `--skip_review` during development iterations

## Conclusion

The `launch_scientist_bfts.py` script represents a sophisticated orchestration of multiple AI systems working together to conduct autonomous scientific research. From initial hypothesis to peer-reviewed paper, it demonstrates the potential for AI to augment and automate complex research workflows while maintaining scientific rigor and reproducibility.
