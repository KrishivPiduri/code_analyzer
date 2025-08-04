from cost_constants import *
from utils import analyze_chunks_average
from cost_calculations import calculate_phase1_costs, calculate_phase2_costs, calculate_phase3_costs, calculate_cost

import os

def analyze_project_latex(project_root: str, entry_file: str = None, project_name: str = None) -> str:
    """Generate LaTeX table format for cost breakdown"""
    if project_name is None:
        project_name = os.path.basename(project_root).upper()

    if entry_file is None:
        entry_file = os.path.join(project_root, "__init__.py")
        if not os.path.isfile(entry_file):
            python_files = []
            for root, _, files in os.walk(project_root):
                for file in files:
                    if file.endswith(".py"):
                        python_files.append(os.path.join(root, file))
            entry_file = python_files[0] if python_files else ""

    chunk_analysis = analyze_chunks_average(project_root)
    avg_chunk_tokens = chunk_analysis['avg_tokens_per_chunk']
    total_tokens = chunk_analysis['total_tokens']
    files_processed = chunk_analysis['files_processed']
    avg_tokens_per_file = total_tokens / files_processed if files_processed > 0 else 0

    phase1_costs = calculate_phase1_costs(chunk_analysis)
    phase2_costs = calculate_phase2_costs(avg_chunk_tokens=avg_chunk_tokens)

    # Baseline strategy: input tokens = avg_chunk_tokens * 3
    baseline_input_tokens = int(avg_chunk_tokens * 3)
    baseline_output_tokens = int(avg_chunk_tokens)
    baseline_input_cost = calculate_cost(baseline_input_tokens, CLAUDE_INPUT_COST_PER_KTOK)
    baseline_output_cost = calculate_cost(baseline_output_tokens, CLAUDE_OUTPUT_COST_PER_KTOK)
    baseline_total = baseline_input_cost + baseline_output_cost

    # Chunk-based retrieval (our approach)
    chunk_input_tokens = int(phase2_costs['input_tokens_used'])
    chunk_output_tokens = int(phase2_costs['output_tokens_used'])
    chunk_total = phase2_costs['total_per_prompt']

    # One-time costs
    embedding_cost = phase1_costs['embedding_cost']
    parsing_cost = phase1_costs['summarization_input_cost'] + phase1_costs['summarization_output_cost']

    latex_output = f"""\\begin{{table}}[htbp]
\\caption{{Cost Breakdown for {project_name}}}
\\resizebox{{\\columnwidth}}{{!}}{{%
\\begin{{tabular}}{{|l|r|r|r|}}
\\hline
\\textbf{{Strategy}} & \\textbf{{Input Tokens}} & \\textbf{{Output Tokens}} & \\textbf{{Cost (USD)}} \\\\
\\hline
Baseline & {baseline_input_tokens} & {baseline_output_tokens} & {baseline_total:.4f} \\\\
\\textbf{{Chunk-Based Retrieval (Ours)}} & {chunk_input_tokens} & {chunk_output_tokens} & {chunk_total:.6f} \\\\
\\hline
\\multicolumn{{4}}{{|l|}}{{\\textbf{{One-Time Costs (Ours only)}}}} \\\\
\\hline
Embedding Generation & -- & -- & {embedding_cost:.4f} \\\\
Parsing Cost & -- & -- & {parsing_cost:.4f} \\\\
\\hline
\\end{{tabular}}
}}
\\label{{tab:cost_{project_name}}}
\\end{{table}}"""

    return latex_output

def analyze_project_comprehensive(project_root: str, entry_file: str = None) -> str:
    if entry_file is None:
        entry_file = os.path.join(project_root, "__init__.py")
        if not os.path.isfile(entry_file):
            python_files = []
            for root, _, files in os.walk(project_root):
                for file in files:
                    if file.endswith(".py"):
                        python_files.append(os.path.join(root, file))
            entry_file = python_files[0] if python_files else ""

    chunk_analysis = analyze_chunks_average(project_root)
    avg_chunk_tokens = chunk_analysis['avg_tokens_per_chunk']
    total_tokens = chunk_analysis['total_tokens']
    files_processed = chunk_analysis['files_processed']
    avg_tokens_per_file = total_tokens / files_processed if files_processed > 0 else 0
    avg_tokens_per_project = total_tokens

    phase1_costs = calculate_phase1_costs(chunk_analysis)
    phase2_costs = calculate_phase2_costs(avg_chunk_tokens=avg_chunk_tokens)
    phase3_costs = calculate_phase3_costs(avg_chunk_tokens=avg_chunk_tokens)
    storage = phase1_costs['storage_details']

    strategy1_input_cost = calculate_cost(avg_tokens_per_file, CLAUDE_INPUT_COST_PER_KTOK)
    strategy1_output_cost = calculate_cost(avg_chunk_tokens, CLAUDE_OUTPUT_COST_PER_KTOK)
    strategy1_total = strategy1_input_cost + strategy1_output_cost
    strategy2_input_cost = calculate_cost(avg_tokens_per_project, CLAUDE_INPUT_COST_PER_KTOK)
    strategy2_output_cost = calculate_cost(avg_chunk_tokens, CLAUDE_OUTPUT_COST_PER_KTOK)
    strategy2_total = strategy2_input_cost + strategy2_output_cost

    # Strategy 3: Input = avg file tokens + 2x avg chunk tokens, Output = 1x avg chunk tokens
    strategy3_input_tokens = avg_tokens_per_file + 2 * avg_chunk_tokens
    strategy3_input_cost = calculate_cost(strategy3_input_tokens, CLAUDE_INPUT_COST_PER_KTOK)
    strategy3_output_cost = calculate_cost(avg_chunk_tokens, CLAUDE_OUTPUT_COST_PER_KTOK)
    strategy3_total = strategy3_input_cost + strategy3_output_cost

    markdown_output = f"""
# Comprehensive Code Analyzer Cost Breakdown

## Project Statistics
- **Files Processed**: {chunk_analysis['files_processed']:,}
- **Total Chunks**: {chunk_analysis['total_chunks']:,}
- **Total Tokens**: {chunk_analysis['total_tokens']:,}
- **Average Tokens per Chunk**: {avg_chunk_tokens:.1f}
- **Average Tokens per File**: {avg_tokens_per_file:.1f}

## Storage Requirements
- **Raw Code Storage**: {storage['raw_code_gb']:.3f} GB
- **Summary Storage**: {storage['summary_storage_gb']:.3f} GB
- **Vector Embeddings**: {storage['vector_storage_gb']:.3f} GB
- **Metadata Storage**: {storage['metadata_storage_gb']:.3f} GB

---

## 📌 Phase 1: One-Time Indexing Costs

| Component | Cost | Details |
|-----------|------|---------|
| **LLM Summarization (Input)** | ${phase1_costs['summarization_input_cost']:.4f} | {chunk_analysis['total_chunks']:,} chunks × {avg_chunk_tokens:.0f} tokens |
| **LLM Summarization (Output)** | ${phase1_costs['summarization_output_cost']:.4f} | {chunk_analysis['total_chunks']:,} summaries × 150 tokens |
| **Embedding Generation** | ${phase1_costs['embedding_cost']:.4f} | {chunk_analysis['total_chunks']:,} embeddings |
| **🔸 Total One-Time Cost** | **${phase1_costs['total_one_time']:.4f}** | |

### Monthly Storage Costs
| Storage Type | Cost/Month | Size |
|--------------|------------|------|
| Object Storage (Code) | ${phase1_costs['object_storage_monthly']:.4f} | {storage['raw_code_gb']:.3f} GB |
| Vector Database | ${phase1_costs['vector_db_storage_monthly']:.4f} | {storage['vector_storage_gb']:.3f} GB |
| Metadata Database | ${phase1_costs['metadata_storage_monthly']:.4f} | {storage['metadata_storage_gb']:.3f} GB |
| **🔸 Total Storage/Month** | **${phase1_costs['total_monthly_storage']:.4f}** | |

---

## 🔄 Phase 2: Per-Prompt Costs

| Component | Cost | Details |
|-----------|------|---------|
| **Prompt Parsing (Input)** | ${phase2_costs['prompt_parsing_input_cost']:.6f} | Small LLM for intent extraction |
| **Prompt Parsing (Output)** | ${phase2_costs['prompt_parsing_output_cost']:.6f} | ~50 tokens response |
| **Vector Search** | ${phase2_costs['vector_search_cost']:.6f} | 1 search operation |
| **Prompt Embedding** | ${phase2_costs['prompt_embedding_cost']:.6f} | Embed user query |
| **Code Retrieval** | ${phase2_costs['retrieval_cost']:.6f} | Fetch 3 chunks from storage |
| **Final LLM (Input)** | ${phase2_costs['final_input_cost']:.6f} | {phase2_costs['input_tokens_used']:.0f} tokens (prompt + code) |
| **Final LLM (Output)** | ${phase2_costs['final_output_cost']:.6f} | {phase2_costs['output_tokens_used']} tokens response |
| **🔸 Total Per Prompt** | **${phase2_costs['total_per_prompt']:.6f}** | |

---

## 🔧 Phase 3: Update Costs (when files change)

| Component | Cost | Details |
|-----------|------|---------|
| **File Monitoring** | ${phase3_costs['monitoring_monthly_cost']:.6f}/month | Per file change detection |
| **Re-summarization (Input)** | ${phase3_costs['resummary_input_cost']:.6f} | Process {phase3_costs['affected_chunks']} changed chunks |
| **Re-summarization (Output)** | ${phase3_costs['resummary_output_cost']:.6f} | Generate new summaries |
| **Re-embedding** | ${phase3_costs['reembedding_cost']:.6f} | Update vector embeddings |
| **Database Updates** | ${phase3_costs['db_update_cost']:.6f} | Update vector + metadata DBs |
| **🔸 Total Per Update** | **${phase3_costs['total_per_update']:.6f}** | |

---

## 💰 Cost Summary

### One-Time Setup
- **Initial Indexing**: ${phase1_costs['total_one_time']:.4f}
- **Storage (per month)**: ${phase1_costs['total_monthly_storage']:.4f}

### Ongoing Operations
- **Per Prompt**: ${phase2_costs['total_per_prompt']:.6f}
- **Per File Update**: ${phase3_costs['total_per_update']:.6f}

### Cost Projections
- **100 prompts/day**: ${phase2_costs['total_per_prompt'] * 100:.4f}/day
- **1000 prompts/month**: ${phase2_costs['total_per_prompt'] * 1000:.4f}/month
- **10 file updates/month**: ${phase3_costs['total_per_update'] * 10:.4f}/month

**Total Monthly Cost (1000 prompts + 10 updates)**: ${phase1_costs['total_monthly_storage'] + (phase2_costs['total_per_prompt'] * 1000) + (phase3_costs['total_per_update'] * 10):.4f}

---

## 📊 Per-Query Cost Strategies

| Strategy | Input Tokens | Input Cost | Output Tokens | Output Cost | Total Cost |
|----------|-------------|------------|--------------|-------------|------------|
| Strategy 1 (Avg File) | {avg_tokens_per_file:.0f} | ${strategy1_input_cost:.4f} | {avg_chunk_tokens:.0f} | ${strategy1_output_cost:.4f} | ${strategy1_total:.4f} |
| Strategy 2 (Project) | {avg_tokens_per_project:.0f} | ${strategy2_input_cost:.4f} | {avg_chunk_tokens:.0f} | ${strategy2_output_cost:.4f} | ${strategy2_total:.4f} |
| Strategy 3 (File + 2 Chunks) | {strategy3_input_tokens:.0f} | ${strategy3_input_cost:.4f} | {avg_chunk_tokens:.0f} | ${strategy3_output_cost:.4f} | ${strategy3_total:.4f} |
"""
    return markdown_output


def analyze_project(project_root: str, entry_file: str = None, format_type: str = "markdown") -> str:
    """Analyze project and return results in specified format"""
    if format_type == "latex":
        return analyze_project_latex(project_root, entry_file)
    else:
        return analyze_project_comprehensive(project_root, entry_file)


def main():
    project_root = "tensorflow/tensorflow"
    entry_file = os.path.join(project_root, "__init__.py")
    if not os.path.exists(project_root):
        print(f"Project root '{project_root}' not found. Using current directory.")
        project_root = "."
        entry_file = "combined_analyzer.py"
    if not os.path.isfile(entry_file):
        entry_file = None

    # Generate both formats
    print("=== MARKDOWN FORMAT ===")
    print(analyze_project(project_root, entry_file, "markdown"))
    print("\n=== LATEX FORMAT ===")
    print(analyze_project(project_root, entry_file, "latex"))

if __name__ == "__main__":
    main()
