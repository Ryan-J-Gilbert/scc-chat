RETRIEVAL_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "retrieve_documents",
        "description": "Retrieves both Q&A and detailed article documents about the SCC",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant documents",
                }
            },
            "required": ["query"],
        },
    },
}


def hybrid_retrieve(collection, query, n_results_qa=2, n_results_article=2):
    """Retrieve both types of documents for a given query"""

    # Get QA documents
    qa_results = collection.query(
        query_texts=[query], n_results=n_results_qa, where={"doc_type": "QA"}
    )

    # Get article documents
    article_results = collection.query(
        query_texts=[query], n_results=n_results_article, where={"doc_type": "article"}
    )

    # Combine results
    retrieved_docs = {"qa_documents": [], "article_documents": []}

    # Process Q&A results
    if qa_results["documents"] and len(qa_results["documents"][0]) > 0:
        for i, (doc, metadata) in enumerate(
            zip(qa_results["documents"][0], qa_results["metadatas"][0])
        ):
            retrieved_docs["qa_documents"].append(
                {
                    "content": doc,
                    "source": metadata.get("source", "Unknown"),
                    "distance": (
                        qa_results["distances"][0][i]
                        if "distances" in qa_results
                        else None
                    ),
                }
            )

    # Process article results
    if article_results["documents"] and len(article_results["documents"][0]) > 0:
        for i, (doc, metadata) in enumerate(
            zip(article_results["documents"][0], article_results["metadatas"][0])
        ):
            retrieved_docs["article_documents"].append(
                {
                    "content": doc,
                    "source": metadata.get("source", "Unknown"),
                    "title": metadata.get("title", "Unknown"),
                    "distance": (
                        article_results["distances"][0][i]
                        if "distances" in article_results
                        else None
                    ),
                }
            )

    return retrieved_docs


def retrieve_documents(collection, query):
    """Function called by the tool"""
    return hybrid_retrieve(collection, query)
