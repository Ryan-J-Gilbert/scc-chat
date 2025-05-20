import os
import chromadb
from chromadb.config import Settings
import pandas as pd
from tqdm import tqdm


def get_collection():
    # Initialize ChromaDB client
    dbdir = "/projectnb/scc-chat/research/embeddingsstore"
    print("Building or loading from", dbdir)
    chroma_client = chromadb.PersistentClient(
        settings=Settings(anonymized_telemetry=False), path=dbdir
    )

    # If collection already exists, get it, otherwise create a new one
    try:
        collection = chroma_client.get_collection(name="scc_unified_collection")
        print("Using existing collection")
    except:
        collection = chroma_client.create_collection(name="scc_unified_collection")
        print("Created new collection")

    # Load documents if the collection is empty
    if collection.count() == 0:
        # Load articles
        documents = []
        metadatas = []
        ids = []

        for filename in tqdm(os.listdir("scraped_content"), desc="Loading Articles"):
            if filename.endswith(".md"):
                filepath = os.path.join("scraped_content", filename)
                with open(filepath, "r", encoding="utf-8") as file:
                    content = file.read()

                    documents.append(content)
                    metadatas.append(
                        {"source": filepath, "doc_type": "article", "title": filename}
                    )
                    ids.append(f"article_{filename}")

        print(f"Adding {len(documents)} articles to collection...")
        if documents:
            collection.add(documents=documents, metadatas=metadatas, ids=ids)

        # Load Q&A documents
        documents = []
        metadatas = []
        ids = []

        df = pd.read_excel(
            "../Data/RCSpages_edited_combined_questions_answers_copy1.xlsx"
        )
        for i, row in tqdm(enumerate(df.itertuples()), desc="Loading Q&As"):
            string = f"""Q&A Document
            Question:
            {row.Questions}

            Answer:
            {row.Answers}

            Source:
            {row.Source}
            """
            documents.append(string)
            metadatas.append({"source": row.Source, "doc_type": "QA"})
            ids.append(f"QA_{i}")

        print(f"Adding {len(documents)} Q&A documents to collection...")
        if documents:
            collection.add(documents=documents, metadatas=metadatas, ids=ids)

        print(f"Collection now has {collection.count()} documents total")
    else:
        print(f"Collection already contains {collection.count()} documents")

    return collection
