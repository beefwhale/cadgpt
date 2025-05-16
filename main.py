import os
import logging
from openai import OpenAI
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from embeddings import get_embedding_function
from pathlib import Path

from pocketflow import Node, Flow
from langchain_openai import ChatOpenAI

load_dotenv()
CHROMA_PATH = os.getenv('CHROMA_PATH')
CHROMA_COLLECTION = os.getenv('CHROMA_COLLECTION_DESC')
FILE_PATH = os.getenv('FILE_PATH')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

PROMPT_TEMPLATE = """
You are an expert in CadQuery and Python. Given the following context, generate **only** valid, functional CadQuery code that follows best practices. Ensure the code does not contain syntax errors and is executable.

Context:
{context}

---

Task: Generate CadQuery code for the following request:
{question}

**Guidelines:**
- Use `cq.Workplane` properly.
- Ensure all operations are valid and logically ordered.
- Include necessary imports (`import cadquery as cq`).
- Do not include explanations, only return valid Python code.
- If unsure, return the best possible attempt.
- Use .circle().extrude() instead of .cylinder()
- Use display(object) at the end of the script instead of show() or show_object()
- If creating a symmetrical object, create half of it and use .mirror() to complete it.
- Always ensure that objects are created at the origin (0, 0, 0) unless otherwise specified.

Output only the CadQuery code:
"""

# Ensure USER_AGENT is set
if 'USER_AGENT' not in os.environ:
    os.environ['USER_AGENT'] = "cadgpt"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./credentials.json"

# Setup logging
logging.basicConfig(level=logging.INFO)

# Set up OpenAI API key
OpenAI.api_key = OPENAI_API_KEY

# Define a reusable model creator function
def get_openai_model(temperature=0.2):
    return ChatOpenAI(
        model="o3-mini",
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        reasoning_effort="medium",
    )

class RetrieveContext(Node):
    def prep(self, shared):
        return shared["query"]
    
    def exec(self, query):
        # Get the embedding object
        embedding_function = get_embedding_function()

        # Use it with Chroma
        vector_store = Chroma(
            persist_directory=CHROMA_PATH,
            collection_name=CHROMA_COLLECTION,
            embedding_function=embedding_function
        )

        # When performing similarity search, pass the query as a string
        results = vector_store.similarity_search_with_score(query, k=5)
        return sorted(results, key=lambda x: x[1], reverse=True)
    
    def post(self, shared, prep_res, exec_res):
        context_text = self._build_base_context()
        for chunk in exec_res:
            context_text += "\n\n---\n\n" + chunk[0].page_content
        shared["context"] = context_text
        shared["sources"] = [chunk[0].metadata.get("id", None) for chunk in exec_res]
        return "default"

    def _build_base_context(self):
        return """
        ---
        Example 1:
        Request: Create a cylinder with a 1-inch diameter and 2-inch height.
        Output:
        import cadquery as cq
        result = cq.Workplane("XY").cylinder("2", 0.5, centered=(True, True, False))
        ---

        Example 2:
        Request: Create a nut with a 1/2 inch diameter.
        Output:
        import cadquery as cq
        diameter = 0.5
        height = 0.25
        result = cq.Workplane("XY").circle(diameter / 2).extrude(height)
        .faces("<Z").workplane().hole(diameter / 4)
        ---
        """

class GenerateCode(Node):
    guidelines_path = Path("./documents/cadquery-improvement-guide.md")
    def load_context_from_file(self, file_path):
        try:
            with open(file_path, "r") as file:
                return file.read()
        except Exception as e:
            print(f"Error loading context file: {e}")
            return "No guidelines available."

    def prep(self, shared):
        prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        return prompt_template.format(
            context=self.load_context_from_file(self.guidelines_path), 
            question=shared["query"]
        )
    
    def exec(self, prompt):
        model = get_openai_model(temperature=0.2)
        response = model.invoke(prompt)
        return response.content.strip()
    
    def post(self, shared, prep_res, exec_res):
        shared["code_response"] = exec_res
        return "default"

class SaveToNotebook(Node):
    def prep(self, shared):
        return shared["query"], shared["code_response"]
    
    def exec(self, inputs):
        import os
        import nbformat as nbf
        
        query_text, code_response = inputs
        notebook_dir = "./query"
        notebook_filename = os.path.join(notebook_dir, "result.ipynb")
        code_response_py = code_response.replace("```python","").replace("```","").strip()
        
        # Create directory if it doesn't exist
        os.makedirs(notebook_dir, exist_ok=True)
        
        # Create a new notebook if it doesn't exist
        if not os.path.exists(notebook_filename):
            nb = nbf.v4.new_notebook()
        else:
            try:
                with open(notebook_filename, "r") as f:
                    nb = nbf.read(f, as_version=4)
            except:
                # If file exists but is corrupted/empty, create a new notebook
                nb = nbf.v4.new_notebook()
        
        new_code = "###"+query_text.replace("\n","\n##")+"\n"+code_response_py
        new_code_cell = nbf.v4.new_code_cell(new_code)
        if "id" in new_code_cell:
            del new_code_cell["id"]
        nb.cells.append(new_code_cell)
        
        with open(notebook_filename, "w") as f:
            nbf.write(nb, f)
        return True
    
    def post(self, shared, prep_res, exec_res):
        logging.info(f"\n\n\033[32mResponse: {shared['code_response']}\033[0m\n\nSources: {shared['sources']}]")
        return "default"

class EvaluateContext(Node):
    def prep(self, shared):
        return shared["context"], shared["query"]
    
    def exec(self, inputs):
        context, query = inputs
        model = get_openai_model(temperature=0.0)  # Lower temperature for evaluation
        evaluation = model.invoke(f"Rate how relevant this context is to the query: {query}\n\nContext: {context}")
        return evaluation.content
    
    def post(self, shared, prep_res, exec_res):
        shared["context_evaluation"] = exec_res
        # If evaluation is poor, you could trigger additional retrieval
        return "default"  

class DecomposeTask(Node):
    def prep(self, shared):
        return shared["query"]
    
    def exec(self, query):
        model = get_openai_model(temperature=0.3)
        prompt = f"Break down this CadQuery task into steps: {query}"
        steps = model.invoke(prompt)
        return steps.content
    
    def post(self, shared, prep_res, exec_res):
        shared["task_steps"] = exec_res
        return "default"

class AnalyzeQuery(Node):
    def prep(self, shared):
        return shared["query"]
    
    def exec(self, query):
        model = get_openai_model(temperature=0.1)
        analysis = model.invoke(f"Analyze the type of query: {query}")
        return analysis.content
    
    def post(self, shared, prep_res, exec_res):
        shared["query_type"] = exec_res
        return "default"

class VerifyCode(Node):
    def prep(self, shared):
        return shared["code_response"]
    
    def exec(self, code_response):
        model = get_openai_model(temperature=0.0)  # Lower temperature for verification
        verification = model.invoke(f"Verify the validity of the following CadQuery code:\n\n{code_response}")
        return verification.content
    
    def post(self, shared, prep_res, exec_res):
        shared["code_verification"] = exec_res
        return "default"

def create_cadquery_flow():
    # Create nodes
    retrieve = RetrieveContext()
    analyze = AnalyzeQuery()         # New node to analyze query type
    decompose = DecomposeTask()      # New node to break down complex tasks
    evaluate = EvaluateContext()     # New node to evaluate context quality
    generate = GenerateCode()
    verify = VerifyCode()            # New node to check code validity
    save = SaveToNotebook()
    
    # Connect nodes with branching logic
    analyze >> decompose >> retrieve >> evaluate >> generate >> verify >> save
    
    # Add error handling paths
    evaluate - "insufficient_context" >> retrieve  # Loop back if context is poor
    verify - "invalid_code" >> generate            # Regenerate if code is invalid
    
    return Flow(start=analyze)

def query_rag(query_text: str):
    try:
        flow = create_cadquery_flow()
        shared = {"query": query_text}
        flow.run(shared)
    except Exception as e:
        logging.error(f"An error occurred: {e}")

def main():
    query_text = """
    Write a Python script using CadQuery to create a cylinder with another cylinder twisted to a semicircle and attached to the first cylinder to resemble a parametric mug with a three-circle emblem attached to the front. The script should:
            - Create a base cylinder of diameter 7 inches and height of 7 inches
            - Ensure that the cylinder is a tube with a wall thickness of 0.3 inches and hollow in the center
            - Generate a base plate of 1/2 inch thickness and of same diameter as the cylinder should be attached to the base of the cylinder
            - Generate another cylinder of diameter 1 inch and a length of 3 inches.
            - Ensure that the cylinder is bent from start to end with a bend radius of 1.5 inches creating an open semicircle
            - Ensure that both ends of the bent cylinder are connected to the cylinder's curved exterior surface sitting flush and smoothly at two points aligning with one above another, and centered vertically along the first cylinder's height.
            - Add a three-circle emblem hole from the front of the mug (opposite to the handle):
                - Create the emblem using one large circle (2 inches diameter) for the base and two smaller circles (1 inch diameter each) for the top elements
                - Position the smaller circles at the upper portion of the large circle, evenly spaced apart
                - Ensure the emblem protrudes outward from the mug surface by 0.25 inches
            - Make the emblem solid and ensure it properly fuses with the mug body
            - Include proper imports and documentation
            - Use proper methods available in documentation and do not make your own.
            - Ensure the final object is a valid solid
            - Ensure that the output is displayed with display(item) instead of show_object(item), "item" being the variable name of the final object
    """
    query_rag(query_text)

if __name__ == "__main__":
    main()