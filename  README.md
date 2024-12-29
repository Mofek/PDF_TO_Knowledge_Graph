PMC Search, PDF Extraction, and LLM Knowledge Graph Builder
This repository demonstrates how to:

Search PubMed Central (PMC) via E-utilities for open-access articles based on a user-defined query.
Download the corresponding .tar.gz file from the PMC Open Access (OA) Subset for each article found.
Extract any embedded PDF files from the .tar.gz.
Convert the PDF content to text (via PyPDF2).
Chunk the extracted text.
Generate a Knowledge Graph using an LLM-based transformer.
Upload the resulting entities and relationships into a Neo4j database.
Features
E-utilities (ESearch) for searching PMC:
Retrieves a list of PMC article IDs that match a query (e.g., cancer[tiab] AND open access[filter]).
Open Access File List:
Ensures the official oa_file_list.csv file is locally available (downloading if necessary).
Looks up the .tar.gz path for each PMC ID, confirming the article is in the open-access subset.
PDF Extraction:
Downloads the .tar.gz package for each article.
Extracts only the .pdf files from the tar archive, saving them locally.
Text Conversion and Splitting:
Reads PDF content with PyPDF2, merges page text, and splits into manageable chunks.
LLM-Driven Knowledge Graph:
Uses a Large Language Model (e.g., GPT-4 or GPT-3.5) to transform text chunks into graph documents.
Inserts the generated nodes and relationships into Neo4j.
Prerequisites
Python 3.7+

Dependencies:

requests (for HTTP requests)
PyPDF2 (for PDF parsing)
neo4j or neo4j-driver (depending on your version, for database connectivity)
langchain (or langchain_community, depending on which library provides the LLMGraphTransformer functionality)
openai (if using an OpenAI LLM, or any other library required for your chosen LLM backend)
dotenv (optional, if using a .env file for environment variables)
Install them with:

bash
Copy code
pip install requests PyPDF2 neo4j langchain openai
(Adjust or add libraries according to your environment and requirements.)

Neo4j Database:

You must have a running Neo4j instance.
Obtain the connection URI and credentials (username/password).
Export environment variables:
bash
Copy code
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_PASSWORD="your_neo4j_password"
If your username differs from "neo4j", modify the code accordingly.
LLM Credentials:

If using OpenAI, set:
bash
Copy code
export OPENAI_API_KEY="your_openai_api_key"
export LLM_TYPE="gpt-4"  # or "gpt-3.5-turbo", etc.
Alternatively, configure whichever LLM service you prefer (Hugging Face, local model, etc.).
NCBI E-utilities:

By default, you can make up to 3 requests per second without an API key, 10 with a key.
For large-scale retrieval, consider registering your tool/email with NCBI.
Installation
bash
Copy code
git clone https://github.com/YourUsername/pmc-kg-builder.git
cd pmc-kg-builder
pip install -r requirements.txt
(Create or adapt a requirements.txt to include your dependencies. For example:)

Copy code
requests
PyPDF2
langchain
openai
neo4j
Usage
Set Environment Variables (e.g., in your terminal or via .env file):

bash
Copy code
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_PASSWORD="my_password"
export OPENAI_API_KEY="my_openai_api_key"
export LLM_TYPE="gpt-4"
Modify them to suit your setup.

Run the Script

bash
Copy code
python pmc_search_and_download_pdf.py
or whatever your main script file is named.

Behavior:

Script performs an ESearch on PMC for cancer[tiab] AND open access[filter].
Retrieves up to max_records articles (by default 2, can be changed).
Checks oa_file_list.csv (downloading if not present).
Finds each article’s .tar.gz, downloads it, and extracts PDFs.
For each PDF, extracts text, splits into chunks, and builds a knowledge graph.
Posts the resulting graph entities/relationships to Neo4j.
Output:

PDFs saved to pdf_output/ (by default).
Knowledge graph nodes/edges appear in your Neo4j database.
Logs/prints to the console.
Example Workflow
Search Terms

By default, the script uses cancer[tiab] AND open access[filter].
Adjust query in the code to match your needs (e.g., diabetes[tiab] AND open access[filter]).
Graph Exploration

After completion, open Neo4j Browser at <Your Neo4j address> (usually localhost:7474).
Run Cypher queries, e.g.:
cypher
Copy code
MATCH (n) RETURN n LIMIT 50;
Inspect the nodes and relationships created by the LLMGraphTransformer.
Troubleshooting
No PDFs Found: Some open-access articles only deposit XML, not PDFs. You may see a No PDF found message.
ImportError: If LLMGraphTransformer is not found, update or check your langchain_community library version or confirm the relevant class name.
Rate Limits: For large queries, you may need to throttle your requests or set an api_key for the NCBI E-utilities.
Incomplete Text Extraction: PyPDF2 can sometimes fail on complex PDFs. Check if the PDF is image-based or password-protected. You might need OCR or specialized PDF libraries in such cases.
Contributing
Fork the repository.
Create your feature branch: git checkout -b feature/new-feature.
Commit your changes: git commit -m 'Add some feature'.
Push to the branch: git push origin feature/new-feature.
Open a Pull Request.
License
This project is distributed under the MIT License (or whichever license you choose). Make sure you respect the licenses of any data sets (e.g., open-access only for PMC articles) and the terms for any LLM provider you use.

Contact
For questions or feedback:

Email: My github profile
GitHub Issues: Issue Tracker
NCBI E-utilities information: https://www.ncbi.nlm.nih.gov/books/NBK25499/
