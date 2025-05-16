# CADGPT (v1.0)
Merging CadQuery (a python CAD scripting library) with Generative AI, to create precise and
parametric 3D models while utilizing Retrieval-Augmented Generation (RAG) frameworks and
autonomous workflows to finetune outputs, enabling anyone from hobbyists to industry
professionals to easily create custom and dimensionally accurate models through simple
plaintext descriptions in minutes.

## Setup & User Guide

1. Run `requirements.txt` file to install dependecies.
    ```
    pip install -r requirements.txt
    ```
2. Add your OpenAI API key into `.env`
    ```
    FILE_PATH="documents"
    CHROMA_COLLECTION_CODE="pepe_collection_code" # Description of the code used to generate the items in the collection
    CHROMA_COLLECTION_DESC="pepe_collection_desc" # Description of the items in the collection
    CHROMA_PATH="chroma"
    OPENAI_API_KEY=" " # insert openAI api keyhere
    ```
3. Ensure jupyter notebook file `query/result.ipynb` exists. All outputs go into jupyter notebook.
4. Chunk and save embeddings into local vectorbase (ChromaDB).
    ```
    python3 populate_database.py --reset
    ```
5. Edit and Run query in `main.py`
    ```
    python3 main.py
    ```
6. View output in jupyter book file `query/result.ipynb` by reloading file upon every query output. If nothing appears, ensure that the `display()` method is called with the output variable as the param.


## Stuff you can do

### Make Query

```
python3 main.py
```

### Setup Local ChromaDB

```
python3 populate_database.py 
```

### Reset Local ChromaDB
```
python3 populate_database.py --reset
```
### View DB Items
```
python3 view_database.py
```