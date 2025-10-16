from ..abc import Usecase
import numpy as np
import chromadb
from chromadb.config import Settings
import openai
from typing import List, Dict, Any
from config import get_settings
import fitz
from pydantic import BaseModel

class QueryVariants(BaseModel):
    translation: str
    variants: List[str]

openai.api_key = get_settings().open_ai_api_key
class TreeBasedRag(Usecase):
    def __init__(self, threshold: float, collection_name: str = 'pdf_collection', pdf_path:str = '') -> None:
        self.threshold = threshold
        self.pdf_path = pdf_path
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path="./chroma_data")
        self.collection = self.client.get_collection("pdf_collection")
        self.embed_model = "text-embedding-3-large"
    
    def cosine_similarity(self, a, b):
        """
        a, b: vectors (lists or numpy arrays)
        returns cosine similarity in range [-1, 1]
        """
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))   
    
    def get_doc_name(self) -> List[str]:
        """
        Returns a list of unique document names stored in the collection.
        """
        # Query metadata only
        metadatas = self.collection.get()["metadatas"]

        if not metadatas:
            return []
     
        doc_name = set([str(x['doc_name']) for x in metadatas if x is not None])
        return list(doc_name)

    def embed_text(self, text: str) -> List[float]:
        query_embedding = openai.embeddings.create(
            model=self.embed_model,
            input=text
        ).data[0].embedding

        return query_embedding

    def execute(self, query: str) -> Dict[str,Any] :
        # Step 1: Translate query to English using OpenAI

        client = openai.OpenAI(api_key=get_settings().open_ai_api_key)
        response = client.responses.parse(
            model="gpt-4o-2024-08-06",
            input=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that translates and reformulates queries for information retrieval.",
                },
                {
                    "role": "user",
                    "content": f"""
                    1. Translate the following text into English.
                    2. Then generate 5 concise alternative phrasings of the translated query for use in a retrieval-augmented generation system.
                    3. The output must include:
                        - 'translation': the English version of the query
                        - 'variants': a list of exactly 5 rephrased English queries

                    Text: {query}
                    """,
                },
            ],
            text_format=QueryVariants,
        )

        # Step 3: Access parsed result directly
        data = response.output_parsed
        query_en = (data.translation or '') + ', ' + ', '.join(data.variants) # type: ignore

      
        print(query_en, '\n\n')
        # Step 2: Get embedding of the English query
        query_embedding = self.embed_text(query_en)

        # Step 3: Query the collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=10,
            include=["embeddings", "documents", "metadatas", "distances"],
            where={
                "$or": [
                    {"level": 2},
                    {"level": 3}
                ]
            }
        )


        if not results or not results['embeddings'] or not results['documents'] or not results['metadatas']:
            return {
            "filtered_results": [],
            "page_text": []
        }

        # Step 4: Compute cosine similarities
        cosine_sims = [
            self.cosine_similarity(query_embedding, doc_emb)
            for doc_emb in results['embeddings'][0]
        ]

        # Step 5: Filter results by threshold
        filtered_results = [
            (doc, meta, sim)
            for doc, meta, sim in zip(results['documents'][0], results['metadatas'][0], cosine_sims)
            if sim >= self.threshold
        ]

        # Step 6: getdistinct index
        distinct_start_indices = sorted({meta["start_index"] for _, meta, _ in filtered_results}) # type: ignore
        distinct_end_indices = sorted({meta["end_index"] for _, meta, _ in filtered_results}) # type: ignore
        distinct_indices = list(set(distinct_start_indices + distinct_end_indices))[:3]

        # Step 7: Extract text from PDF based on distinct indices
        page_text_dict = {}

        with fitz.open(self.pdf_path) as pdf:
            for page_num in distinct_indices:
                if page_num is None:
                    continue
                # PyMuPDF pages are 0-indexed
                page_idx = max(page_num - 1, 0)
                if page_idx >= len(pdf):
                    continue  # skip if index out of bounds

                page = pdf.load_page(page_idx)
                text = page.get_text("text").strip() # type: ignore

                if page_num not in page_text_dict:
                    page_text_dict[page_num] = text
                else:
                    # Concatenate if multiple nodes refer to same page
                    page_text_dict[page_num] += "\n" + text

        # Optional: sort by page number
        page_text_dict = dict(sorted(page_text_dict.items()))

        # Step 8: Return results
        return {
            "filtered_results": filtered_results,
            "page_text": page_text_dict
        }

        

        