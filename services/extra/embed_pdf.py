import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import time
import openai
import chromadb
from config import get_settings

# -------------------------------
# 1. OpenAI API Key
# -------------------------------
openai.api_key = get_settings().open_ai_api_key

# -------------------------------
# 2. Load your JSON data
# -------------------------------
with open("transformed_data/Bhatla_structure.json", "r", encoding="utf-8") as f:
    data = json.load(f)


flattened_nodes = []

flattened_nodes = []

def safe_metadata(node):
    return {
        "doc_name": node.get("doc_name") or "",
        "title": node.get("title") or "",
        "node_id": node.get("node_id") or "",
        "parent_id": node.get("parent_id") or "",
        "start_index": node.get("start_index") or 0,
        "end_index": node.get("end_index") or 0,
        "level": node.get("level") or 1
    }

def flatten_nodes(node_list, parent_id=None, level=1, max_level=3):
    for node in node_list:
        if level > max_level:
            continue  # skip nodes deeper than max_level
        flattened_nodes.append({
            "text": node.get("summary") or node.get("title") or "",  # summary > title > ""
            "doc_name": data.get("doc_name", "Unknown.pdf"),
            "title": node.get("title", ""),
            "node_id": node.get("node_id"),
            "parent_id": parent_id,
            "start_index": node.get("start_index"),
            "end_index": node.get("end_index"),
            "level": level
        })
        # Recurse into nested nodes
        if "nodes" in node:
            flatten_nodes(node["nodes"], parent_id=node["node_id"], level=level+1, max_level=max_level)

flatten_nodes(data["structure"])

print(f"Flattened {len(flattened_nodes)} nodes for embedding (up to level 3).")

# Generate embeddings
embeddings = []
for node in flattened_nodes:
    text_to_embed = node["text"] or node["title"] or ""
    response = openai.embeddings.create(
        model="text-embedding-3-large",
        input=text_to_embed
    )
    embeddings.append(response.data[0].embedding)
    time.sleep(0.1)  # avoid hitting rate limits

print("Embeddings generated.")

# ChromaDB setup
client = chromadb.PersistentClient(path="./chroma_data") 
collection_name = "pdf_collection"

try:
    collection = client.get_collection(collection_name)
except:
    collection = client.create_collection(collection_name)

# Add vectors
collection.add(
    ids=[node["node_id"] for node in flattened_nodes],
    documents=[node["text"] for node in flattened_nodes],
    embeddings=embeddings,
    metadatas=[safe_metadata(node) for node in flattened_nodes]
)

print("All nodes added to ChromaDB.")
