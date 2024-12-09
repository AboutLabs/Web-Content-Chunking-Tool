import streamlit as st
import requests
from bs4 import BeautifulSoup
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from langchain.docstore.document import Document
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Use secrets for Azure Form Recognizer credentials
endpoint = st.secrets["azure"]["form_recognizer_endpoint"]
key = st.secrets["azure"]["form_recognizer_key"]

st.title("Web Scraping & Azure Document Intelligence Demo")

url = "https://ppedv.de/Schulung/Kurse/MicrosoftPowerPlatformPowerAppsPowerAutomatePowerBIPowerVirtualAgentM365LowCodeSeminarTrainingWeiterbildungWorkshop"

st.write("**Target URL:**", url)

document_analysis_client = DocumentAnalysisClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)

# Fetch the page content
response = requests.get(url)
if response.status_code == 200:
    html_content = response.text

    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract clean text content
    text_content = soup.get_text(separator='\n', strip=True)

    st.subheader("Extracted Text Content")
    st.write(text_content)

    try:
        # Create PDF from text
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        
        # Split text into lines that fit on the page
        y = 750  # Starting y position
        for line in text_content.split('\n'):
            if y < 50:  # If we're near the bottom of the page
                c.showPage()  # Start a new page
                y = 750  # Reset y position
            
            # Write the line to the PDF
            c.drawString(50, y, line[:100])  # Limit line length to prevent overflow
            y -= 12  # Move down for next line
        
        c.save()
        
        # Move buffer position to start
        pdf_buffer.seek(0)
        
        # Use the PDF file with Azure Document Intelligence
        poller = document_analysis_client.begin_analyze_document(
            "prebuilt-layout",
            document=pdf_buffer
        )
        result = poller.result()

        # Extract all text lines from the result
        extracted_text = []
        for page in result.pages:
            for line in page.lines:
                extracted_text.append(line.content)

        full_text = "\n".join(extracted_text)

        # Create a LangChain Document
        doc = Document(page_content=full_text, metadata={"source": url})

        st.subheader("Raw Text Extracted via Document Intelligence")
        st.text(full_text)

        st.subheader("LangChain Document")
        st.write(doc)

        # Split text into chunks with defined headers
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        
        try:
            chunks = splitter.split_text(doc.page_content)
            
            st.subheader("Chunked Documents (via MarkdownHeaderTextSplitter)")
            for i, chunk in enumerate(chunks):
                st.write(f"**Chunk {i}:**")
                st.write(chunk)
        except Exception as e:
            st.write("No headers found in the text. Using the full text as one chunk.")
            st.write(doc)

        # Alternative approach using RecursiveCharacterTextSplitter
        # text_splitter = RecursiveCharacterTextSplitter(
        #     chunk_size=1000,
        #     chunk_overlap=200,
        #     length_function=len,
        # )
        
        # chunks = text_splitter.split_text(doc.page_content)
        
        # st.subheader("Chunked Documents")
        # for i, chunk in enumerate(chunks):
        #     st.write(f"**Chunk {i}:**")
        #     st.write(chunk)

    except Exception as e:
        # Fixed error display
        st.error(f"Error processing document: {str(e)}")

else:
    st.error(f"Failed to fetch URL. Status code: {response.status_code}")