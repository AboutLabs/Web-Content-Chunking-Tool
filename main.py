import streamlit as st
import requests
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup
import re
from langchain.schema import Document

# App title and description
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
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            if response.status_code == 200:
                st.success("Successfully fetched webpage!")

                # Step 2: Initial HTML Processing
                st.header("2. Raw HTML Content")
                with st.expander("Show Raw HTML"):
                    st.code(response.text[:1000] + "...", language="html")

                # Step 3: BeautifulSoup Processing
                st.header("3. HTML Cleaning")
                soup = BeautifulSoup(response.text, 'html.parser', from_encoding=response.encoding)

                # Show before cleaning
                with st.expander("Before Cleaning"):
                    st.code(soup.get_text()[:1000] + "...", language="text")

                # Remove unwanted elements
                for element in soup.find_all(['script', 'style', 'nav', 'footer', 'iframe', 'noscript']):
                    element.decompose()

                # Show after removing elements
                with st.expander("After Removing Unwanted Elements"):
                    st.code(soup.get_text()[:1000] + "...", language="text")

                # Step 4: Converting to Markdown Format
                st.header("4. Converting to Markdown Format")

                # Process headings
                for i in range(1, 7):
                    for heading in soup.find_all(f'h{i}'):
                        heading.string = f"\n{'#' * i} {heading.get_text().strip()}\n"

                # Improved list processing function
                def process_list_items(list_elem, prefix=''):
                    items = []
                    for i, li in enumerate(list_elem.find_all('li', recursive=False), 1):
                        # Handle nested lists
                        nested_lists = li.find_all(['ul', 'ol'], recursive=False)
                        content = li.get_text().strip()

                        # Remove nested list text from content
                        for nested in nested_lists:
                            content = content.replace(nested.get_text(), '')

                        # Add list item with proper prefix
                        if isinstance(list_elem, soup.find('ol').__class__):
                            items.append(f"{prefix}{i}. {content.strip()}")
                        else:
                            items.append(f"{prefix}* {content.strip()}")

                        # Process nested lists with increased indentation
                        for nested in nested_lists:
                            nested_items = process_list_items(nested, prefix + '  ')
                            items.extend(nested_items)

                    return items

                # Process all lists
                for list_elem in soup.find_all(['ul', 'ol']):
                    if list_elem.parent.name not in ['ul', 'ol']:  # Only process top-level lists
                        processed_items = process_list_items(list_elem)
                        list_elem.string = '\n' + '\n'.join(processed_items) + '\n'

                # Process paragraphs
                for p in soup.find_all('p'):
                    if not p.find_parent(['ul', 'ol']):
                        p.string = f"{p.get_text().strip()}\n\n"

                # Extract and clean text content
                text_content = soup.get_text(separator='\n', strip=True)
                text_content = re.sub(r'\n\s*\n', '\n\n', text_content)

                # Show markdown formatted text
                with st.expander("Markdown Formatted Text"):
                    st.markdown(text_content[:1000] + "...")

                # Show processed lists separately
                with st.expander("Show Processed Lists"):
                    lists = soup.find_all(['ul', 'ol'])
                    for i, lst in enumerate(lists, 1):
                        if lst.parent.name not in ['ul', 'ol']:
                            st.markdown(f"**List {i}:**")
                            st.markdown(lst.get_text())
                            st.markdown("---")

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
                    "Beratung via Chat",
                    "Support Chat",
                    "remember Passwort vergessen",
                    "Cookies akzeptieren"
                ]

                # Split and filter content
                lines = text_content.split('\n')
                filtered_lines = []
                skip_section = False

                for line in lines:
                    # Check if line contains unwanted section header
                    is_unwanted_section = any(
                        re.search(rf"^#+\s*{re.escape(section)}", line, re.IGNORECASE)
                        for section in sections_to_remove
                    ) or any(
                        section.lower() in line.lower()
                        for section in sections_to_remove
                    )

                    if is_unwanted_section:
                        skip_section = True
                        continue

                    if re.match(r'^#+\s', line) and not is_unwanted_section:
                        skip_section = False

                    if not skip_section:
                        filtered_lines.append(line)

                # Join filtered lines
                text_content = '\n'.join(filtered_lines)

                # Show filtered content
                with st.expander("Filtered Content"):
                    st.markdown(text_content[:1000] + "...")

                # Step 5: Text Splitting Process
                st.header("5. Text Splitting Process")
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
                    # Header-based splitting
                    header_chunks = header_splitter.split_text(text_content)

                    with st.expander("Header-Based Chunks"):
                        for i, chunk in enumerate(header_chunks):
                            st.markdown(f"**Chunk {i+1}**")
                            st.json(chunk.metadata)
                            st.markdown(chunk.page_content[:200] + "...")
                            st.markdown("---")

                    # Final splitting
                    final_chunks = []
                    for chunk in header_chunks:
                        if len(chunk.page_content) > 500:
                            smaller_chunks = recursive_splitter.split_text(chunk.page_content)
                            for small_chunk in smaller_chunks:
                                final_chunks.append(Document(page_content=small_chunk, metadata=chunk.metadata))
                        else:
                            final_chunks.append(chunk)

                    with st.expander("Final Processed Chunks"):
                        for i, chunk in enumerate(final_chunks):
                            st.markdown(f"**Chunk {i+1}**")
                            st.markdown("*Metadata:*")
                            st.json(chunk.metadata)
                            st.markdown("*Content:*")
                            st.markdown(chunk.page_content)
                            st.markdown("---")

                    # Statistics
                    st.header("6. Processing Statistics")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Text Length", len(text_content))
                    with col2:
                        st.metric("Number of Chunks", len(final_chunks))
                    with col3:
                        avg_chunk_size = sum(len(chunk.page_content) for chunk in final_chunks) / len(final_chunks)
                        st.metric("Avg Chunk Size", f"{avg_chunk_size:.0f}")

                except Exception as e:
                    st.warning("No headers found in the text. Using content-based splitting only.")
                    chunks = recursive_splitter.split_text(text_content)
                    with st.expander("Content-Based Chunks"):
                        for i, chunk in enumerate(chunks):
                            st.markdown(f"**Chunk {i+1}**")
                            st.markdown(chunk)
                            st.markdown("---")

        except requests.RequestException as e:
            st.error(f"Failed to fetch webpage: {str(e)}")
        except Exception as e:
            st.error(f"Processing error: {str(e)}")