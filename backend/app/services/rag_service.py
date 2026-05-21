from uuid import uuid4

import ollama

from fastembed import TextEmbedding

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)


COLLECTION_NAME = "clinical_cases"

client = QdrantClient(
    url="http://localhost:6333"
)

embedding_model = TextEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)


def create_collection_if_not_exists():
    collections = client.get_collections().collections

    collection_names = [
        collection.name for collection in collections
    ]

    if COLLECTION_NAME not in collection_names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )


def chunk_text(text: str, chunk_size: int = 800):
    words = text.split()
    chunks = []

    for index in range(0, len(words), chunk_size):
        chunk = " ".join(
            words[index:index + chunk_size]
        )

        if chunk.strip():
            chunks.append(chunk)

    return chunks


def index_case_text(
    case_id: int,
    case_title: str,
    text: str
):
    create_collection_if_not_exists()

    chunks = chunk_text(text)

    if not chunks:
        return {
            "status": "empty",
            "case_id": case_id,
            "chunks": 0
        }

    embeddings = list(
        embedding_model.embed(chunks)
    )

    points = []

    for chunk, vector in zip(chunks, embeddings):
        points.append(
            PointStruct(
                id=str(uuid4()),
                vector=vector.tolist(),
                payload={
                    "case_id": case_id,
                    "case_title": case_title,
                    "text": chunk
                }
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    return {
        "status": "indexed",
        "case_id": case_id,
        "chunks": len(points)
    }


def search_cases(query: str, limit: int = 5):
    create_collection_if_not_exists()

    query_vector = list(
        embedding_model.embed([query])
    )[0]

    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector.tolist(),
        limit=limit
    )

    return [
        {
            "case_id": item.payload.get("case_id"),
            "case_title": item.payload.get("case_title"),
            "text": item.payload.get("text"),
            "score": item.score
        }
        for item in results
    ]


def answer_with_rag(query: str, limit: int = 5):
    results = search_cases(query, limit)

    context = "\n\n".join(
        [
            f"Case: {item['case_title']}\nContent: {item['text']}"
            for item in results
        ]
    )

    prompt = f"""
You are a clinical teaching assistant.

Answer the question using ONLY the provided clinical case context.

Rules:
- Do not hallucinate.
- If context is insufficient, say "Insufficient case context available."
- Use clear medical teaching language.

Clinical Case Context:
{context}

Question:
{query}
"""

    response = ollama.chat(
        model="mistral",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0.2
        }
    )

    return {
        "answer": response["message"]["content"],
        "sources": results
    }