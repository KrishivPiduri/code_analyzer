import os
import json
from astchunk import ASTChunkBuilder

def chunk_python_files_in_directory(directory_path, output_json_path):
    configs = {
        "max_chunk_size": 100,  # Maximum non-whitespace characters per chunk
        "language": "python",  # Supported: python, java, csharp, typescript
        "metadata_template": "default"  # Metadata format for output
    }
    chunk_builder = ASTChunkBuilder(**configs)
    all_chunks = []

    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                chunks = chunk_builder.chunkify(code)
                for i, chunk in enumerate(chunks):
                    all_chunks.append({
                        'file': file_path,
                        'chunk_index': i + 1,
                        'content': chunk['content'],
                        'metadata': chunk['metadata'],
                        'raw_code': code
                    })
    with open(output_json_path, 'w', encoding='utf-8') as out_f:
        json.dump(all_chunks, out_f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    chunk_python_files_in_directory("url-shortener", "chunks_output.json")
