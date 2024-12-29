#!/usr/bin/env python3


import os
import csv
import time
import requests
import tarfile
import PyPDF2

# For LLM chunking and knowledge graph building
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chat_models import ChatOpenAI
from langchain_community.graphs.neo4j_graph import Neo4jGraph

############################
# Step 0: LLM + Neo4j Setup
############################

def get_llm():
    
    
    model_name = os.getenv("LLM_TYPE", "gpt-4")  
    openai_api_key = os.getenv("OPENAI_API_KEY", "my_openai_api_key")
    llm = ChatOpenAI(
        temperature=0,
        model=model_name,
        openai_api_key=openai_api_key
    )
    return llm

def build_neo4j_connection():
    
    uri = os.environ["NEO4J_URI"]  
    password = os.environ["NEO4J_PASSWORD"]
   
    graph = Neo4jGraph(
        url=uri,
        username="neo4j",
        password=password
    )
    return graph

############################
# Step A: ESearch in PMC
############################

def esearch_pmc(term, email, api_key=None, tool="MyPythonScript", retmax=10):
    """
    eSarches PMC (PubMed Central) for articles matching the given term.
    Returns a list of PMC IDs (e.g., "PMC1234567").

    :param term:    (str) Query, e.g. "cancer[tiab] AND open access[filter]"
    :param email:   (str) Required by NCBI
    :param api_key: (str) NCBI API key for higher rates (optional)
    :param tool:    (str) Name of your tool or script
    :param retmax:  (int) Maximum articles to retrieve
    :return:        (list) A list of PMC IDs
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pmc",
        "term": term,
        "email": email,
        "tool": tool,
        "retmode": "xml",
        "retmax": retmax
    }
    if api_key:
        params["api_key"] = api_key

    print(f"[ESearch] Searching PMC for: {term}")
    r = requests.get(base_url, params=params, timeout=30)
    r.raise_for_status()

    # Parse IDs from returned XML
    pmc_ids = []
    for line in r.text.splitlines():
        line = line.strip()
        if line.startswith("<Id>") and line.endswith("</Id>"):
            pmcid = line.replace("<Id>", "").replace("</Id>", "")
            if not pmcid.upper().startswith("PMC"):
                pmcid = "PMC" + pmcid
            pmc_ids.append(pmcid)

    return pmc_ids

############################
# Step B: Download + Parse OA File List
############################

def ensure_file_list_downloaded(file_list_url, local_csv="oa_file_list.csv"):
    """
    Downloads the PMC OA file list if not already present locally.
    """
    if os.path.exists(local_csv):
        print(f"[FileList] Found existing {local_csv}. Not downloading again.")
        return local_csv

    print(f"[FileList] Downloading file list from: {file_list_url}")
    with requests.get(file_list_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(local_csv, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"[FileList] Saved to {local_csv}")
    return local_csv

def find_article_tar_gz_in_filelist(csv_path, pmc_id):
    """
    Search the local CSV file for the row containing pmc_id.
    Return the relative path to the .tar.gz package or None if not found.
    """
    found_path = None
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)  # might be a timestamp or header
        # print(f"[FileList] Header/First line: {header}")
        for row in reader:
            if len(row) < 3:
                continue
            if row[2].strip() == pmc_id:
                found_path = row[0]  # the .tar.gz path
                break
    return found_path

############################
# Step C: Download .tar.gz from PMC FTP, Extract PDF
############################

def download_file(url, local_filename):
    
    print(f"[Download] Fetching: {url}")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"[Download] Saved to {local_filename}")

def extract_pdf_from_tar(tar_path, output_dir="pdf_output"):
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    extracted_pdfs = []
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.isfile() and member.name.lower().endswith(".pdf"):
                print(f"[Extract] Found PDF: {member.name}")
                tar.extract(member, path=output_dir)
                extracted_path = os.path.join(output_dir, member.name)
                extracted_pdfs.append(extracted_path)
    return extracted_pdfs

############################
# Step D: Extract Text from PDFs, Chunk, Build KG
############################

def extract_text_from_pdf(pdf_path):
    """
    Extract all text from a PDF using PyPDF2, returning it as a single string.
    """
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    return text

def build_kg_from_text(text, llm, graph_connection):
    
    if not text.strip():
        print("[KG] No text to process.")
        return

    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=24)
    documents = text_splitter.split_documents([Document(page_content=text)])

    
    llm_transformer = LLMGraphTransformer(llm=llm)

    graph_documents = llm_transformer.convert_to_graph_documents(documents[:20])

    print(f"[KG] Generated {len(graph_documents)} graph documents. Uploading to Neo4j...")

    
    graph_connection.add_graph_documents(
        graph_documents,
        baseEntityLabel=True,
        include_source=True
    )
    

    print("[KG] Upload complete.")

############################
# Main
############################

def main():
    # ESearch in PMC
    email = ""   # Required by NCBI
    api_key = ""                     # or "YOUR_API_KEY" if you have one
    query = ""
    max_records = 1  # How many articles to fetch from ESearch

    pmc_ids = esearch_pmc(query, email, api_key=api_key, retmax=max_records)
    if not pmc_ids:
        print("[Main] No articles found for this query.")
        return
    print(f"[Main] Found {len(pmc_ids)} PMC IDs: {pmc_ids}")

    # Download the PMC OA file list to verify .tar.gz location
    FILELIST_URL = "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_file_list.csv"
    local_csv = ensure_file_list_downloaded(FILELIST_URL)

    # Neo4j + LLM setup
    llm = get_llm()
    graph_conn = build_neo4j_connection()

    BASE_FTP = "https://ftp.ncbi.nlm.nih.gov/pub/pmc/"

    # For each PMC ID, see if it's in the file list, then download + extract PDF
    for pmcid in pmc_ids:
        print(f"\n[Main] Processing {pmcid}...")
        tar_gz_relative_path = find_article_tar_gz_in_filelist(local_csv, pmcid)
        if not tar_gz_relative_path:
            print(f"[Main] {pmcid} not found in oa_file_list.csv or not open access. Skipping.")
            continue

        # Download .tar.gz for that PMC article
        tar_url = os.path.join(BASE_FTP, tar_gz_relative_path) 
        local_tar = f"{pmcid}.tar.gz"
        download_file(tar_url, local_tar)

        # Extract PDF
        pdf_files = extract_pdf_from_tar(local_tar, output_dir="pdf_output")
        if not pdf_files:
            print(f"[Main] No PDF found for {pmcid}. Possibly only XML or supplementary files.")
           
            continue

        # For each extracted PDF, read text and build a knowledge graph
        for pdf_file in pdf_files:
            print(f"[Main] Extracting text from PDF: {pdf_file}")
            pdf_text = extract_text_from_pdf(pdf_file)
            if not pdf_text.strip():
                print("[Main] PDF text is empty or unreadable.")
                continue

            print("[Main] Building KG from PDF text...")
            build_kg_from_text(pdf_text, llm, graph_conn)

        

    print("[Main] Done.")


if __name__ == "__main__":
    main()
