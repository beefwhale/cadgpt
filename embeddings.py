from langchain_openai import OpenAIEmbeddings

import os
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = os.getenv('CHROMA_PATH')
CHROMA_COLLECTION = os.getenv('CHROMA_COLLECTION_DESC')

def get_embedding_function():
    """Returns an OpenAIEmbeddings object that can be used with Chroma"""
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )

