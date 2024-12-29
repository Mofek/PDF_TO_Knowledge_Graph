program Overview
This program automates the retrieval of open-access articles from PubMed Central (PMC), extracts PDF files from each downloaded package, and transforms the extracted text into a knowledge graph. The process involves:

Searching PMC for articles matching specified criteria (e.g., open-access or containing certain keywords).
Downloading article packages in .tar.gz format from the official PMC Open Access Subset.
Extracting PDF files from the downloaded archive, then converting the PDF text into manageable chunks.
Generating a knowledge graph from these text chunks using a large language model (LLM), identifying entities and relationships for further analysis.
By combining these steps, the program offers a streamlined way to gather, parse, and structure scholarly content for more efficient discovery and analysis.
