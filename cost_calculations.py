from cost_constants import *
from utils import count_tokens

def calculate_cost(tokens: float, cost_per_ktok: float) -> float:
    return (tokens / 1000) * cost_per_ktok

def estimate_storage_sizes(chunk_analysis: dict, avg_summary_tokens: int = 150) -> dict:
    total_chunks = chunk_analysis['total_chunks']
    avg_chunk_tokens = chunk_analysis['avg_tokens_per_chunk']
    raw_code_gb = chunk_analysis['size'] / (1024**3)
    summary_storage_gb = (total_chunks * avg_summary_tokens * 4) / (1024**3)
    vector_storage_gb = (total_chunks * 1536 * 4) / (1024**3)
    metadata_storage_gb = (total_chunks * 1024) / (1024**3)
    return {
        'raw_code_gb': max(raw_code_gb, 0.001),
        'summary_storage_gb': max(summary_storage_gb, 0.001),
        'vector_storage_gb': max(vector_storage_gb, 0.001),
        'metadata_storage_gb': max(metadata_storage_gb, 0.001),
        'total_chunks': total_chunks,
        'avg_summary_tokens': avg_summary_tokens
    }

def calculate_phase1_costs(chunk_analysis: dict, avg_summary_tokens: int = 150) -> dict:
    total_chunks = chunk_analysis['total_chunks']
    avg_chunk_tokens = chunk_analysis['avg_tokens_per_chunk']
    storage = estimate_storage_sizes(chunk_analysis, avg_summary_tokens)
    summarization_input_cost = calculate_cost(total_chunks * avg_chunk_tokens, CLAUDE_INPUT_COST_PER_KTOK)
    summarization_output_cost = calculate_cost(total_chunks * avg_summary_tokens, CLAUDE_OUTPUT_COST_PER_KTOK)
    embedding_cost = calculate_cost(total_chunks * avg_summary_tokens, EMBEDDING_COST_PER_KTOK)
    object_storage_monthly = storage['raw_code_gb'] * OBJECT_STORAGE_COST_PER_GB_MONTH
    vector_db_storage_monthly = storage['vector_storage_gb'] * VECTOR_DB_STORAGE_COST_PER_GB_MONTH
    metadata_storage_monthly = storage['metadata_storage_gb'] * METADATA_DB_STORAGE_COST_PER_GB_MONTH
    total_one_time = summarization_input_cost + summarization_output_cost + embedding_cost
    total_monthly_storage = object_storage_monthly + vector_db_storage_monthly + metadata_storage_monthly
    return {
        'summarization_input_cost': summarization_input_cost,
        'summarization_output_cost': summarization_output_cost,
        'embedding_cost': embedding_cost,
        'object_storage_monthly': object_storage_monthly,
        'vector_db_storage_monthly': vector_db_storage_monthly,
        'metadata_storage_monthly': metadata_storage_monthly,
        'total_one_time': total_one_time,
        'total_monthly_storage': total_monthly_storage,
        'storage_details': storage
    }

def calculate_phase2_costs(avg_prompt_tokens: int = 100, avg_response_tokens: int = 500, chunks_retrieved: int = 3, avg_chunk_tokens: float = 200) -> dict:
    prompt_parsing_input_cost = calculate_cost(avg_prompt_tokens, PROMPT_PARSING_LLM_INPUT_COST_PER_KTOK)
    prompt_parsing_output_cost = calculate_cost(50, PROMPT_PARSING_LLM_OUTPUT_COST_PER_KTOK)
    vector_search_cost = VECTOR_SEARCH_COST_PER_1K_OPS / 1000
    prompt_embedding_cost = calculate_cost(avg_prompt_tokens, PROMPT_EMBEDDING_COST_PER_KTOK)
    retrieval_cost = chunks_retrieved * OBJECT_RETRIEVAL_COST_PER_REQUEST
    final_input_tokens = avg_prompt_tokens + (chunks_retrieved * avg_chunk_tokens)
    final_input_cost = calculate_cost(final_input_tokens, CLAUDE_INPUT_COST_PER_KTOK)
    final_output_cost = calculate_cost(avg_chunk_tokens, CLAUDE_OUTPUT_COST_PER_KTOK)
    total_per_prompt = (prompt_parsing_input_cost + prompt_parsing_output_cost + vector_search_cost + prompt_embedding_cost + retrieval_cost + final_input_cost + final_output_cost)
    return {
        'prompt_parsing_input_cost': prompt_parsing_input_cost,
        'prompt_parsing_output_cost': prompt_parsing_output_cost,
        'vector_search_cost': vector_search_cost,
        'prompt_embedding_cost': prompt_embedding_cost,
        'retrieval_cost': retrieval_cost,
        'final_input_cost': final_input_cost,
        'final_output_cost': final_output_cost,
        'total_per_prompt': total_per_prompt,
        'input_tokens_used': final_input_tokens,
        'output_tokens_used': avg_chunk_tokens
    }

def calculate_phase3_costs(files_changed: int = 1, avg_chunks_per_file: int = 10, avg_chunk_tokens: float = 200, avg_summary_tokens: int = 150) -> dict:
    monitoring_monthly_cost = files_changed * FILE_MONITORING_COST_PER_FILE_MONTH
    affected_chunks = files_changed * avg_chunks_per_file
    resummary_input_cost = calculate_cost(affected_chunks * avg_chunk_tokens, CLAUDE_INPUT_COST_PER_KTOK)
    resummary_output_cost = calculate_cost(affected_chunks * avg_summary_tokens, CLAUDE_OUTPUT_COST_PER_KTOK)
    reembedding_cost = calculate_cost(affected_chunks * avg_summary_tokens, UPDATE_EMBEDDING_COST_PER_KTOK)
    db_update_cost = affected_chunks * 2 * DB_UPDATE_COST_PER_OPERATION
    total_per_update = resummary_input_cost + resummary_output_cost + reembedding_cost + db_update_cost
    return {
        'monitoring_monthly_cost': monitoring_monthly_cost,
        'resummary_input_cost': resummary_input_cost,
        'resummary_output_cost': resummary_output_cost,
        'reembedding_cost': reembedding_cost,
        'db_update_cost': db_update_cost,
        'total_per_update': total_per_update,
        'affected_chunks': affected_chunks
    }

