import os
from astchunk import ASTChunkBuilder

def chunk_python_files_in_directory(directory_path):
    configs = {
        "max_chunk_size": 100,  # Maximum non-whitespace characters per chunk
        "language": "python",  # Supported: python, java, csharp, typescript
        "metadata_template": "default"  # Metadata format for output
    }
    chunk_builder = ASTChunkBuilder(**configs)

    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                print(f"\n=== File: {file_path} ===")
                chunks = chunk_builder.chunkify(code)
                for i, chunk in enumerate(chunks):
                    print(f"[Chunk {i + 1}]")
                    print(f"{chunk['content']}")
                    print(f"Metadata: {chunk['metadata']}")
                    print("-" * 50)

if __name__ == "__main__":
    chunk_python_files_in_directory("url-shortener")
