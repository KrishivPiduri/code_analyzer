import os
import ast
import tiktoken
from typing import List, Dict

tokenizer = tiktoken.encoding_for_model("gpt-4")

def count_tokens(text: str) -> int:
    return len(tokenizer.encode(text))

def get_python_files(directory: str) -> List[str]:
    py_files = []
    size=0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
                size+= os.path.getsize(os.path.join(root, file))
    return py_files, size

def split_by_ast_nodes(source: str) -> List[Dict]:
    chunks = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    lines = source.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start_line = node.lineno - 1
            end_line = max(getattr(node, 'end_lineno', start_line + 1), start_line + 1)
            chunk_lines = lines[start_line:end_line]
            chunk_code = "\n".join(chunk_lines)
            token_count = count_tokens(chunk_code)
            chunks.append({
                'start_line': start_line + 1,
                'end_line': end_line,
                'token_count': token_count,
                'type': type(node).__name__,
                'code': chunk_code
            })
    return chunks

def analyze_chunks_average(directory: str) -> Dict:
    total_tokens = 0
    total_chunks = 0
    files, size = get_python_files(directory)
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                source = f.read()
            except Exception:
                continue
        chunks = split_by_ast_nodes(source)
        total_chunks += len(chunks)
        total_tokens += sum(chunk['token_count'] for chunk in chunks)
    avg_tokens_per_chunk = total_tokens / total_chunks if total_chunks > 0 else 0
    return {
        'files_processed': len(files),
        'total_chunks': total_chunks,
        'total_tokens': total_tokens,
        'size': size,
        'avg_tokens_per_chunk': avg_tokens_per_chunk
    }

