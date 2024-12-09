import streamlit as st
import requests
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup
import re
from langchain.schema import Document

# Add this at the start, right after the imports
st.set_page_config(page_title="📝 Web Content Chunking Tool")
st.title("📝 Web Content Chunking Tool")
st.subheader("Converts ppedv course websites into structured, analyzable chunks")

# Get the URL from user input
default_url = "https://ppedv.de/Schulung/Kurse/MicrosoftPowerPlatformPowerAppsPowerAutomatePowerBIPowerVirtualAgentM365LowCodeSeminarTrainingWeiterbildungWorkshop"
url = st.text_input("Enter the webpage URL:", value=default_url)
analyze_button = st.button("Analyze")

if analyze_button:
    if not url.startswith(('http://', 'https://')):
        st.error("Please enter a valid URL starting with http:// or https://")
    else:
        try:
            # Step 1: Fetch webpage
            st.header("1. Fetching Webpage")
            response = requests.get(url)
            if response.status_code == 200:
                st.success("Successfully fetched webpage!")

                # Step 2: Initial HTML Processing
                st.header("2. Raw HTML Content")
                with st.expander("Show Raw HTML"):
                    st.code(response.text[:1000] + "...", language="html")

                # Step 3: BeautifulSoup Processing
                st.header("3. HTML Cleaning")
                soup = BeautifulSoup(response.text, 'html.parser')

                # Show before cleaning
                with st.expander("Before Cleaning"):
                    st.code(soup.get_text()[:1000] + "...", language="text")

                # Remove unwanted elements
                for element in soup.find_all(['script', 'style', 'nav', 'footer']):
                    element.decompose()

                # Show after removing elements
                with st.expander("After Removing Unwanted Elements"):
                    st.code(soup.get_text()[:1000] + "...", language="text")

                # Step 4: Converting to Markdown
                st.header("4. Converting to Markdown Format")

                # Convert headings to markdown format
                for i in range(1, 7):
                    for heading in soup.find_all(f'h{i}'):
                        heading.string = f"{'#' * i} {heading.get_text()}\n"

                # Process paragraphs
                for p in soup.find_all('p'):
                    p.string = f"{p.get_text()}\n\n"

                # Extract and clean text content
                text_content = soup.get_text(separator='\n', strip=True)
                text_content = re.sub(r'\n\s*\n', '\n\n', text_content)

                # Show markdown formatted text before section removal
                with st.expander("Before Removing Sections"):
                    st.markdown(text_content[:1000] + "...")

                # Remove unwanted sections
                sections_to_remove = [
                    "ppedv Erfahrungen",
                    "Kundenbewertungen",
                    "Weitere Kurse zum Thema",
                    "Ihr Kontakt",
                    "Häufige Fragen",
                    "Ihre Vorteile",
                    "Ihr .* Event",
                    "my ppedv Login",
                    "Feedback per Mail senden",
                    "Schulungszentren",
                    "Cookie Warnung",
                    "Beratung via Chat"
                ]

                # Split content into lines for processing
                lines = text_content.split('\n')
                filtered_lines = []
                skip_section = False

                for line in lines:
                    # Check if line is a header of sections to remove
                    is_unwanted_section = any(
                        re.match(f"^#+\s*{section}", line, re.IGNORECASE)
                        for section in sections_to_remove
                    ) or any(
                        section.lower() in line.lower()
                        for section in ["remember Passwort vergessen", "Cookie Warnung", "Cookies akzeptieren", "Support Chat"]
                    )

                    if is_unwanted_section:
                        skip_section = True
                        continue

                    # Check if we've reached a new section (any header)
                    if re.match(r'^#+\s', line) and not is_unwanted_section:
                        skip_section = False

                    if not skip_section:
                        filtered_lines.append(line)

                # Join the filtered lines back together
                text_content = '\n'.join(filtered_lines)

                # Show after removing sections
                with st.expander("After Removing Sections"):
                    st.markdown(text_content[:1000] + "...")

                # Step 5: Text Splitting Process
                st.header("5. Text Splitting Process")

                # Header-based splitting
                headers_to_split_on = [
                    ("#", "Title"),
                    ("##", "Section"),
                    ("###", "Subsection"),
                    ("####", "Subsubsection")
                ]

                header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
                recursive_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,
                    chunk_overlap=50,
                    separators=["\n\n", "\n", ". ", " ", ""],
                    length_function=len,
                )

                try:
                    # First split by headers
                    st.subheader("5.1 Header-Based Splits")
                    header_chunks = header_splitter.split_text(text_content)

                    with st.expander("Show Header-Based Chunks"):
                        for i, chunk in enumerate(header_chunks):
                            st.markdown(f"**Chunk {i+1}**")
                            st.json(chunk.metadata)
                            st.markdown(chunk.page_content[:200] + "...")
                            st.markdown("---")

                    # Then split large sections
                    st.subheader("5.2 Final Chunks (with recursive splitting)")
                    final_chunks = []
                    for chunk in header_chunks:
                        chunk_metadata = chunk.metadata
                        chunk_content = chunk.page_content

                        if len(chunk_content) > 500:
                            smaller_chunks = recursive_splitter.split_text(chunk_content)
                            for small_chunk in smaller_chunks:
                                final_chunks.append(Document(
                                    page_content=small_chunk,
                                    metadata=chunk_metadata
                                ))
                        else:
                            final_chunks.append(chunk)

                    with st.expander("Show Final Processed Chunks"):
                        for i, chunk in enumerate(final_chunks):
                            st.markdown(f"**Chunk {i+1}**")
                            st.markdown("*Metadata:*")
                            st.json(chunk.metadata)
                            st.markdown("*Content:*")
                            st.markdown(chunk.page_content)
                            st.markdown("---")

                except Exception as e:
                    st.warning("No headers found in the text. Using content-based splitting only.")
                    chunks = recursive_splitter.split_text(text_content)

                    with st.expander("Show Content-Based Chunks"):
                        for i, chunk in enumerate(chunks):
                            st.markdown(f"**Chunk {i+1}**")
                            st.markdown(chunk)
                            st.markdown("---")

                # Step 6: Statistics
                st.header("6. Processing Statistics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Text Length", len(text_content))
                with col2:
                    st.metric("Number of Chunks", len(final_chunks))
                with col3:
                    avg_chunk_size = sum(len(chunk.page_content) for chunk in final_chunks) / len(final_chunks)
                    st.metric("Avg Chunk Size", f"{avg_chunk_size:.0f}")

            else:
                st.error(f"Failed to fetch the webpage. Status code: {response.status_code}")

        except Exception as e:
            st.error(f"Error occurred: {str(e)}")