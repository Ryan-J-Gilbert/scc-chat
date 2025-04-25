import os
import chromadb
from chromadb.config import Settings
import pandas as pd
from tqdm import tqdm

# disabling telemetry -> will this be an issue?
chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))

collection = chroma_client.create_collection(name="my_collection")
documents = []
metadatas = []
ids = []

for filename in tqdm(os.listdir('scraped_content'), desc="Loading Articles"):
    # print(f"Loading {filename}...")
    if filename.endswith(".md"):
        filename = os.path.join('scraped_content', filename)
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()

            documents.append(content)
            metadatas.append({
                "source": filename,
                "doc_type": "article"
            })
            ids.append(f"doc_{filename}")

print("Vectorizing...")
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)


df = pd.read_excel("../Data/RCSpages_edited_combined_questions_answers_copy1.xlsx")
documents = []
metadatas = []
ids = []

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
    metadatas.append({
        "source": row.Source,
        "doc_type": "QA"
    })
    ids.append(f"QA_{i}")

print("Vectorizing...")
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)



while True:
    prompt = input("Query: ")

    for n_results, doc_type in [(1,'article'), (2,'QA')]:
        results = collection.query(
            query_texts=[prompt], # Chroma will embed this for you
            n_results=n_results, # how many results to return
            where={"doc_type": doc_type},
        )
        # print(prompt)
        # print(results)
        for index, i in enumerate(results['documents'][0]):
            print('='*100)
            print("Document", index)
            print("Metadata: ", results['metadatas'][0][index])
            print(i)
            print('='*100)
            print()