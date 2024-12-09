# 🌐 Web Content Analyzer & Chunker

A powerful Streamlit-based tool designed to convert web content into search-optimized chunks, perfect for AI processing and semantic search applications.

## 🎯 Key Features
- **Smart Web Scraping**: Automatically fetches and cleans web content
- **Intelligent Content Processing**: Converts HTML to structured Markdown
- **Advanced Chunking**: Uses LangChain's smart text splitting algorithms
- **Metadata Preservation**: Maintains document structure and hierarchy
- **Search-Ready Output**: Creates chunks optimized for Azure AI Search
- **Interactive UI**: Real-time visualization of processing steps

## 🚀 Getting Started

### Prerequisites
- Python 3.10
- Poetry (for dependency management)

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/web-content-analyzer.git
# Install dependencies using Poetry
poetry install
```

### Running the App
```bash
poetry run streamlit run main.py
```

### 💡 Usage
1. Enter a URL in the input field
2. Click "Analyze" to start processing
3. View the results in expandable sections:
   - Raw HTML content
   - Cleaned content
   - Markdown conversion
   - Final chunks with metadata

## 🔧 Technical Details
- Built with Streamlit, BeautifulSoup4, and LangChain
- Uses advanced text splitting algorithms
- Supports both header-based and content-based chunking
- Preserves document structure and metadata
- Ready for integration with Azure AI Search

## 📊 Output Format
Each chunk includes:
```json
{
    "content": "Processed text content",
    "metadata": {
        "Title": "Document title",
        "Section": "Section name",
        "Subsection": "Subsection name"
    }
}
```

## 🤝 Contributing
Contributions welcome! Please feel free to submit a Pull Request.

## 📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments
- Built with Streamlit
- Text processing powered by LangChain
- HTML parsing using BeautifulSoup4

---

This README:
1. Clearly presents the tool's purpose and capabilities
2. Provides easy-to-follow setup instructions
3. Includes technical details and usage examples
4. Uses emojis and formatting for better readability
5. Highlights integration capabilities with Azure AI Search
6. Encourages community participation

Feel free to customize it further based on your specific needs!