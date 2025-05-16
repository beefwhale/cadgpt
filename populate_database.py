import argparse
import os
import shutil
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from langchain_chroma import Chroma
import chromadb
from embeddings import get_embedding_function
from dotenv import load_dotenv
import re
import pymupdf as fitz

from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import Language

load_dotenv()


# FILE_PATH = os.getenv('FILE_PATH')
FILE_PATH = "./documents/"
CHROMA_COLLECTION_CODE = os.getenv('CHROMA_COLLECTION_CODE')
CHROMA_COLLECTION_DESC = os.getenv('CHROMA_COLLECTION_DESC')
CHROMA_PATH = os.getenv('CHROMA_PATH')

# Ensure USER_AGENT is set
if 'USER_AGENT' not in os.environ:
    os.environ['USER_AGENT'] = "cadgpt"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./credentials.json"

def main():
    # Check if the database should be cleared (using the --reset flag).
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()
    if args.reset:
        print("✨ Clearing Database")
        clear_database()
    
    # Load documents
    print(f"File path is: {FILE_PATH}")
    pages = load_documents(FILE_PATH)
    
    # Split documents into code and descriptions
    split_docs = split_with_overlap(pages, 1000, 200)
    
    # Add to Chroma
    add_to_chroma(split_docs, CHROMA_COLLECTION_DESC)

def extract_and_merge_blocks(file_path):
    doc = fitz.open(file_path)
    merged_chunks = []
    buffer = ""  # Store temporary text for merging
    metadata = {}

    for page_num in range(len(doc)):
        blocks = doc[page_num].get_text("blocks")  # Extract structured text blocks
        
        for block in blocks:
            text = block[4].strip()  # Extract text content
            metadata = {"page": page_num + 1, "source": file_path}

            if is_code_block(text):  
                # Merge buffer (previous text) with code
                if buffer:
                    merged_chunks.append(Document(
                        page_content=buffer + "\n\n" + text,  # Merge description with code
                        metadata=metadata
                    ))
                    buffer = ""  # Reset buffer
                else:
                    merged_chunks.append(Document(page_content=text, metadata=metadata))
            else:
                # Store description text in buffer for potential merging
                if buffer:
                    buffer += "\n\n" + text
                else:
                    buffer = text
    
    # Add remaining buffer content if it wasn't merged
    if buffer:
        merged_chunks.append(Document(page_content=buffer, metadata=metadata))

    return merged_chunks

def is_code_block(text):
    """Detects if a text block is a code block (fenced or indented)."""
    return bool(re.match(r"(?s)(```.*?```|(?:^\s{4}.*(?:\n|\r))+)", text))

def load_documents(directory_path):
    def load_language_documents(directory):
        loader = GenericLoader.from_filesystem(
                directory,
                glob='*',
                suffixes=['.py'],
                parser=LanguageParser(Language.PYTHON)
            )
        return loader.load()

    supported_extensions = ['.md', '.pdf']
    documents = []
    code = [] # For future use, to store code blocks separately from descriptions

    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            if os.path.isfile(file_path) and any(filename.endswith(ext) for ext in supported_extensions):
                print("Loading file:", file_path)
                if filename.endswith('.md'):
                    with open(file_path, 'r') as file:
                        content = file.read()
                        documents.append(Document(page_content=content, metadata={"source": file_path}))
                elif filename.endswith('.pdf'):
                    pages = extract_and_merge_blocks(file_path)
                    documents.extend(pages)
    
    documents.extend(load_language_documents(directory_path + "cadquery-contrib/"))
    documents.extend(load_language_documents(directory_path + "cq-warehouse/"))
    documents.extend(load_language_documents("./query"))
    
    if not documents:
        raise ValueError("No supported documents found in the directory. Only .md, .pdf, and .py are supported.")
    
    return documents

def split_with_overlap(docs, chunk_size=500, chunk_overlap=100):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", "```"],  # Preserve paragraph/code grouping and fenced code blocks
    )
    
    split_docs = []
    for doc in docs:
        chunks = []
        current_chunk = ""
        in_code_block = False

        for line in doc.page_content.splitlines(keepends=True):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block

            if in_code_block:
                current_chunk += line
            else:
                if len(current_chunk) + len(line) > chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = line
                else:
                    current_chunk += line

        if current_chunk:
            chunks.append(current_chunk)

        for chunk in chunks:
            split_docs.append(Document(
                page_content=chunk,
                metadata=doc.metadata  # Retain metadata
            ))
    
    return split_docs

def extract_code_blocks(text):
    code_blocks = []
    current_block = []
    in_code_block = False
    inside_fenced_block = False

    for line in text.splitlines():
        # Detect Markdown fenced code blocks
        if re.match(r'^\s*```', line):
            if inside_fenced_block:
                # Close the fenced code block
                code_blocks.append("\n".join(current_block))
                current_block = []
                inside_fenced_block = False
            else:
                inside_fenced_block = True
                current_block = []
            continue
        
        # Detect indented code (heuristic)
        if re.match(r'^\s{4,}', line) or inside_fenced_block:
            if not in_code_block:
                in_code_block = True
                current_block = []
            current_block.append(line)
        else:
            if in_code_block:
                in_code_block = False
                code_blocks.append("\n".join(current_block))
    
    # Handle last block
    if in_code_block or inside_fenced_block:
        code_blocks.append("\n".join(current_block))

    return code_blocks


def add_to_chroma(chunks: list[Document], collection_name):
    persistent_client = chromadb.PersistentClient()
    vector_store = Chroma(
        client=persistent_client,
        collection_name=collection_name,
        embedding_function=get_embedding_function()
    )
    
    chunks_with_ids = calculate_chunk_ids(chunks)
    existing_items = vector_store.get(include=[])
    existing_ids = set(existing_items["ids"])
    
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)
    
    if len(new_chunks):
        print(f"👉 Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        vector_store.add_documents(new_chunks, ids=new_chunk_ids)
    else:
        print("✅ No new documents to add")

def calculate_chunk_ids(chunks):
    last_page_id = None
    current_chunk_index = 0
    
    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"
        
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0
        
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id
        chunk.metadata["id"] = chunk_id
    
    return chunks

def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

if __name__ == "__main__":
    main()