
<h2 align="center">OptSkills: Learning Generalizable Optimization Skills from Problem Archetypes via Cluster-Based Distillation </h2>
<p align="center">
    <a href="https://github.com/fujiwaranoM0kou"><strong>Haochen Yang</strong></a><sup>1,*</sup>
    ·
    <a href="https://github.com/ZhaoKe1024"><strong>Ke Zhao</strong></a><sup>1,*</sup>
    ·
    <a href="#"><strong>Mengyuan Ma</strong></a><sup>1</sup>
    ·
    <a href="#"><strong>Xingyu Lu</strong></a><sup>3</sup>
    <br>
    <a href="#"><strong>Xiangfeng Wang</strong></a><sup>1</sup>
    ·
    <a href="https://github.com/HQian-AI"><strong>Hong Qian</strong></a><sup>1,2,†</sup>
    <div align='center'>
        <sup>*</sup>Equal Contribution, <sup>†</sup>Corresponding Authors.
    </div>
    <p align="center">
        <b>East China Normal University<sup>1</sup>    |    Shanghai Innovation Institute<sup>2</sup>   |   AntGroup<sup>3</sup>  </b></p> 
    <p align="center">
        <a href="http://arxiv.org/abs/2605.29829"><img src='https://img.shields.io/badge/Paper-OptSkills-red'></a>
        <!-- <a href='https://huggingface.co/ant-opt/LLMOPT-Qwen2.5-14B'><img src='https://img.shields.io/badge/%F0%9F%A4%97%20HuggingFace-Model-yellow'></a>
        <!-- <a href=''><img src='https://img.shields.io/badge/%F0%9F%A4%97%20HuggingFace-Dataset-yellow'></a> -->
        <!-- <a href='https://github.com/antgroup/LLMOPT/tree/main/data/testset'><img src='https://img.shields.io/badge/Dataset-Testset-blue'></a> -->
        <a href='https://github.com/fujiwaranoM0kou/OptSkills'><img src='https://img.shields.io/badge/GitHub-Repo-blue'></a>
  </p>  
</p>
<p align="center">
  <img src="./assets/framework.png" alt="Framework" width="1000">
</p>

OptSkills is a skill enhanced agent system for
natural-language optimization tasks. It uses a function-calling
LLM agent to formulate and solve problems with Python solver backends, while
maintaining reusable optimization skills.

## Installation
### Gurobi License
Gurobi requires a valid license. See [Gurobi Academic Licensing](https://www.gurobi.com/academics).

### Prerequisites
- Python 3.12.12
- Conda

### Setup
```bash
#clone this repository
cd OptSkills
#conda create
conda env create -f environment.yml
conda activate optskills
# Linux/macOS
cp .env.example .env
# Windows PowerShell
# Copy-Item .env.example .env
```

### Environment Configuration
| Variable | Meaning | Example |
|---|---|---|
| `OPTSKILL_BASE_URL` | OpenAI-compatible chat-completions API base URL. | `https://api.deepseek.com/v1` |
| `OPTSKILL_API_KEY` | API key for the chat model. | `sk-...` |
| `OPTSKILL_MODEL` | Chat model identifier exposed by the provider. | `deepseek-chat` |
| `OPTSKILL_EMBED_BASE_URL` | OpenAI-compatible embeddings API base URL. | `https://api.openai.com/v1` |
| `OPTSKILL_EMBED_API_KEY` | API key for the embedding endpoint. | `sk-...` |
| `OPTSKILL_EMBED_MODEL` | Embedding model identifier. | `text-embedding-3-large` |

## Repository Layout

```text
OptSkills/
|-- main.py                         # Command-line entry point
|-- environment.yml                 # Reproducible Conda environment and solver dependencies
|-- agents/                         # Function-calling agent and rollout orchestration
|-- llm/                            # Chat and embedding API clients
|-- pipeline/                       # Stage runners, dataset loading, outputs, and resume logic
|-- prompts/                        # Extractor, solver-agent, and skill prompts
|-- skill_core/                     # Skill extraction, clustering, selection, and refinement
|-- tools/                          # Tool registration and run_code exposure
|-- utils/                          # Logging, parsing, code execution, and skill syntax utilities
|-- lists/
|   `-- solvers/                    # Solver catalog exposed to the rollout agent
|       |-- ortools/
|       `-- pyomo/
|-- skill_library/                  # Released skill libraries
|   |-- skill_library_cluster/
|   |-- skill_library_learned/
|   `-- skill_library_nanoco_learned/
`-- datasets/
    |-- train_set/                  # Training datasets, including Nano-CO
    `-- benchmark/                  # Evaluation benchmarks, including MIPLIB-NL
```

## Usage

### 1. Construct an Initial Library (`cluster`)
The following command takes the first 150 instances of `optmath-train-300.jsonl` as the
clustering subset and saves the split definition into the run state.

```bash
python main.py --phase cluster \
  --data datasets/train_set/optmath-train-300.jsonl \
  --run-dir outputs/optmath_train/cluster \
  --cluster-size 150 \
  --cluster-eps 0.05 \
  --cluster-min-samples 1 \
  --cluster-workers 8 \
  --analysis-workers 8 \
  --builder-workers 4 \
  --archetype-fusion-alpha 0.55 \
  --top-k 3 \
  --timeout 120 \
  --agent-max-turns 12 \
  --resume
```

Relevant controls:

| Argument | Meaning |
|---|---|
| `--cluster-size` | Number of training instances assigned to initial clustering. |
| `--cluster-eps`, `--cluster-min-samples` | DBSCAN parameters over archetype embeddings. |
| `--archetype-fusion-alpha` | Fusion weight used when constructing archetype embeddings. |
| `--cluster-workers` | Concurrent initial trajectory collection workers. |
| `--analysis-workers` | Concurrent trajectory analyses within skill distillation. |
| `--builder-workers` | Concurrent cluster-to-skill draft builders; library writes remain deterministic and serialized. |

### 2. Self-Learn from Remaining Training Instances (`learning`)

When `--parent-run-dir` is used with the same training JSONL, learning
automatically processes only the items not assigned to the cluster subset.
For the command above, that is the remaining 150 OptMath instances.

```bash
python main.py --phase learning \
  --data datasets/train_set/optmath-train-300.jsonl \
  --run-dir outputs/optmath_learning \
  --parent-run-dir outputs/optmath_train/cluster \
  --top-k 3 \
  --timeout 120 \
  --agent-max-turns 12 \
  --resume
```

To start learning from an arbitrary released library rather than a cluster run,
provide `--source-skill-library` instead:

```bash
python main.py --phase learning \
  --data datasets/train_set/optmath-train-300.jsonl \
  --run-dir outputs/optmath_learning \
  --source-skill-library skill_library/skill_library_cluster \
  --resume
```

### 3. Evaluate Without Updating Skills (`eval`)

```bash
python main.py --phase eval \
  --data datasets/benchmark/optmath_bench.jsonl \
  --run-dir outputs/eval/optmath \
  --source-skill-library outputs/optmath_learning/skill_library \
  --eval-workers 8 \
  --top-k 3 \
  --timeout 120 \
  --agent-max-turns 12 \
  --resume
```

If `--source-skill-library` is omitted, evaluation uses
`skill_library/skill_library_learned`.

### Outputs and Resume

Each `--run-dir` stores `trajectories.jsonl`, `resume.json`, and `runtime_logs/`.
The `cluster` and `learning` phases additionally store their current
`skill_library/`, while `learning` saves committed skill states under
`checkpoints/`. With `--resume`, learning restores the latest committed
checkpoint before processing remaining samples.

Evaluate MIPLIB-NL using a released library:

```bash
python main.py --phase eval \
  --miplib-nl-bench \
  --data datasets/benchmark/MIPLIB-NL/dataset \
  --run-dir outputs/eval/miplib_nl \
  --source-skill-library skill_library/skill_library_learned \
  --eval-workers 8 \
  --resume
```

## Released Skill Libraries

| Library | Description |
|---|---|
| `skill_library/skill_library_cluster` | Initial skills distilled from clustered solved trajectories. |
| `skill_library/skill_library_learned` | Default learned library for standard evaluation. |
| `skill_library/skill_library_nanoco_learned` | Learned library extended with Nano-CO trajectories. |

## Performance

OptSkills performs remarkably across 5 benchmarks.

*Comparison of the SA metric (Pass@1) across five benchmarks. OptSkills-DeepSeek and OptSkills-Qwen are based on DeepSeek-V3.2 and Qwen3-235B-A22b-instruct-2507, respectively. **Bold** indicates 1st, *italic* indicates 2nd, and <u>underline</u> indicates 3rd.*

| Category | Models / Methods | Macro-Avg. | Micro-Avg. | Rank | OptiBench | Mamo.Complex | OptMATH | IndustryOR | ComplexOR |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| General Models | GPT-5.4 | 51.71 | 57.82 | 6 | 69.09 | 47.39 | 46.39 | 29.00 | *66.67* |
| General Models | Gemini-3.1-Pro | 53.58 | 57.88 | 5 | 66.56 | 46.45 | <u>54.22</u> | <u>34.00</u> | *66.67* |
| General Models | Qwen3-235B | 42.63 | 52.36 | 7 | 63.80 | 41.71 | 39.76 | 29.00 | 38.89 |
| General Models | DeepSeek-V3.2 | 43.21 | 49.45 | 9 | 62.64 | 27.49 | 40.36 | 30.00 | 55.56 |
| Agent-based Methods | Chain-of-Experts | 38.84 | 52.36 | 8 | 62.31 | 51.66 | 35.54 | 28.00 | 16.67 |
| Agent-based Methods | OptiMUS | 34.14 | 45.18 | 13 | 60.99 | 27.49 | 22.89 | 26.00 | 33.33 |
| Agent-based Methods | ORMind | 36.69 | 47.37 | 11 | 61.82 | 34.60 | 21.69 | 32.00 | 33.33 |
| Agent-based Methods | ORThought | 41.92 | 46.91 | 12 | 57.69 | 38.86 | 26.51 | 31.00 | 55.56 |
| Agent-based Methods | LEAN-LLM-OPT | 41.23 | 49.27 | 10 | 62.15 | 43.13 | 22.89 | 28.00 | 50.00 |
| Agent-based Methods | AlphaOPT | 50.92 | 58.55 | 4 | 70.25 | <u>54.50</u> | 36.75 | 32.00 | 61.11 |
| Skill-based Methods | Trace2Skill | <u>56.97</u> | <u>63.46</u> | <u>2</u> | <u>75.21</u> | *54.03* | 49.40 | <u>34.00</u> | **72.22** |
| Skill-based Methods | OptSkills-Qwen | *54.64* | *61.46* | *3* | *71.74* | 53.55 | <u>54.22</u> | 27.00 | *66.67* |
| Skill-based Methods | OptSkills-DeepSeek | **62.04** | **68.27** | **1** | **77.02** | **63.51** | **61.45** | **36.00** | **72.22** |

=======
## 💭 Citation

If you find this repository useful in your research, please cite:

```bibtex
@misc{yang2026optskillslearninggeneralizableoptimization,
      title={OptSkills: Learning Generalizable Optimization Skills from Problem Archetypes via Cluster-Based Distillation}, 
      author={Haochen Yang and Ke Zhao and Mengyuan Ma and Xingyu Lu and Xiangfeng Wang and Hong Qian},
      year={2026},
      eprint={2605.29829},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2605.29829}, 
}
```
