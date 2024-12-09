import streamlit as st
import requests
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup
import re

# Get the URL from user input
url = st.text_input("Enter the webpage URL:")
if url:
    if not url.startswith(('http://', 'https://')):
        st.error("Please enter a valid URL starting with http:// or https://")
    else:
        try:
            # Make the HTTP request
            response = requests.get(url)
            
            if response.status_code == 200:
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Remove unwanted elements
                for element in soup.find_all(['script', 'style', 'nav', 'footer']):
                    element.decompose()
                
                # Convert headings to markdown format
                for i in range(1, 7):
                    for heading in soup.find_all(f'h{i}'):
                        heading.string = f"{'#' * i} {heading.get_text()}\n"
                
                # Process paragraphs and other content
                for p in soup.find_all('p'):
                    p.string = f"{p.get_text()}\n\n"
                
                # Extract structured text content
                text_content = soup.get_text(separator='\n', strip=True)
                
                # Clean up multiple newlines and spaces
                text_content = re.sub(r'\n\s*\n', '\n\n', text_content)
                
                st.subheader("Extracted Text Content")
                st.write(text_content)

                try:
                    # Create PDF and process with Azure DI as before...
                    # After getting the document content in doc.page_content:

                    # First, split by headers
                    headers_to_split_on = [
                        ("#", "Title"),
                        ("##", "Section"),
                        ("###", "Subsection"),
                        ("####", "Subsubsection")
                    ]

                    header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

                    # Then use recursive splitter for long sections
                    recursive_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=500,
                        chunk_overlap=50,
                        separators=["\n\n", "\n", ". ", " ", ""],
                        length_function=len,
                    )

                    try:
                        # First split by headers
                        header_chunks = header_splitter.split_text(text_content)

                        final_chunks = []
                        # Then split large sections into smaller chunks while preserving headers
                        for chunk in header_chunks:
                            # Keep the metadata (headers)
                            chunk_metadata = chunk.metadata
                            chunk_content = chunk.page_content

                            # If the chunk is too large, split it further
                            if len(chunk_content) > 500:
                                smaller_chunks = recursive_splitter.split_text(chunk_content)
                                # Add the header metadata to each sub-chunk
                                for small_chunk in smaller_chunks:
                                    final_chunks.append(Document(
                                        page_content=small_chunk,
                                        metadata=chunk_metadata
                                    ))
                            else:
                                final_chunks.append(chunk)

                        st.subheader("Structured Document Chunks")
                        for i, chunk in enumerate(final_chunks):
                            st.markdown("---")
                            st.markdown(f"**Chunk {i+1}**")
                            # Display the headers if present
                            for header_type, header_content in chunk.metadata.items():
                                st.markdown(f"*{header_type}*: {header_content}")
                            st.markdown("**Content:**")
                            st.write(chunk.page_content)

                    except Exception as e:
                        st.write("No headers found. Using recursive splitting only.")
                        chunks = recursive_splitter.split_text(text_content)

                        st.subheader("Document Chunks (Content-based)")
                        for i, chunk in enumerate(chunks):
                            st.markdown("---")
                            st.markdown(f"**Chunk {i+1}:**")
                            st.write(chunk)

                except Exception as e:
                    st.error(f"Error processing document: {str(e)}")

            else:
                st.error(f"Failed to fetch the webpage. Status code: {response.status_code}")
                
        except Exception as e:
            st.error(f"Error occurred: {str(e)}")