import os
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

print(f"Default Cache Dir: {os.environ.get('LLAMA_INDEX_CACHE_DIR', 'Not Set')}")
try:
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    print("Embedding model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
