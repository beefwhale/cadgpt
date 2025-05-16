import os
from langchain_chroma import Chroma
import chromadb
from dotenv import load_dotenv
load_dotenv()

CHROMA_COLLECTION = os.getenv('CHROMA_COLLECTION_DESC')

persistent_client = chromadb.PersistentClient()
collection = persistent_client.get_or_create_collection(CHROMA_COLLECTION)
# Retrieve all documents and embeddings
documents = collection.get()

# include=["documents", "embeddings", "metadatas", "ids"]
print(documents["metadatas"])