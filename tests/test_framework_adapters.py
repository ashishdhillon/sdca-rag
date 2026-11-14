"""Unit tests for LangChain (SDCATextSplitter) and LlamaIndex (SDCANodeParser) adapters."""

from pathlib import Path
import pytest

from sdca.langchain import SDCATextSplitter
from sdca.llamaindex import SDCANodeParser


@pytest.fixture(scope="module")
def sample_pdf_paths():
    base = Path("data/multi_domain")
    fin = base / "financial_10k_sample.pdf"
    leg = base / "commercial_contract_sample.pdf"
    assert fin.exists()
    assert leg.exists()
    return fin, leg


class TestLangChainAdapter:
    def test_split_pdf(self, sample_pdf_paths):
        fin_path, _ = sample_pdf_paths
        splitter = SDCATextSplitter(target_tokens=300)
        docs = splitter.split_pdf(fin_path)

        assert len(docs) >= 3
        # Check standard LangChain Document interface
        for d in docs:
            assert hasattr(d, "page_content")
            assert hasattr(d, "metadata")
            assert len(d.page_content) > 0
            assert "section" in d.metadata
            assert "section_path" in d.metadata
            assert "token_count" in d.metadata
            assert "source" in d.metadata

        # Verify financial statements were kept intact
        ops_found = any("Subscription Revenue" in d.page_content and "Net Income" in d.page_content for d in docs)
        assert ops_found, "Statement of Operations was not found intact in a single LangChain Document"

    def test_split_pdf_use_retrieval_text(self, sample_pdf_paths):
        _, leg_path = sample_pdf_paths
        splitter = SDCATextSplitter(target_tokens=300, use_retrieval_text=True)
        docs = splitter.split_pdf(leg_path)

        assert len(docs) >= 3
        # If use_retrieval_text=True, page_content should contain the Section prefix
        with_section_prefix = sum(1 for d in docs if "[Section:" in d.page_content)
        assert with_section_prefix > 0

    def test_split_documents(self, sample_pdf_paths):
        from langchain_core.documents import Document as LCDoc
        fin_path, _ = sample_pdf_paths

        # Test with a LangChain document pointing to a PDF file on disk
        input_doc = LCDoc(page_content="Placeholder", metadata={"source": str(fin_path), "custom_tag": "financial_filing"})
        splitter = SDCATextSplitter(target_tokens=300)
        split_docs = splitter.split_documents([input_doc])

        assert len(split_docs) >= 3
        for d in split_docs:
            assert d.metadata.get("custom_tag") == "financial_filing"
            assert "section" in d.metadata

    def test_split_text(self):
        splitter = SDCATextSplitter(target_tokens=300)
        raw_text = (
            "1. Introduction\n\nThis is a research document introducing SDCA.\n\n"
            "2. Methodology\n\nWe present structure-aware chunking without neural models."
        )
        chunks = splitter.split_text(raw_text)
        assert len(chunks) >= 1
        assert any("Introduction" in c or "Methodology" in c for c in chunks)

    def test_create_documents(self):
        splitter = SDCATextSplitter(target_tokens=300)
        texts = ["1. Section A\n\nBody content of section A.", "1. Section B\n\nBody content of section B."]
        metas = [{"doc_id": "doc_1"}, {"doc_id": "doc_2"}]
        docs = splitter.create_documents(texts, metas)

        assert len(docs) >= 2
        assert docs[0].metadata["doc_id"] == "doc_1"


class TestLlamaIndexAdapter:
    def test_parse_pdf(self, sample_pdf_paths):
        fin_path, _ = sample_pdf_paths
        parser = SDCANodeParser(target_tokens=300)
        nodes = parser.parse_pdf(fin_path)

        assert len(nodes) >= 3
        # Check standard LlamaIndex TextNode interface
        for n in nodes:
            assert hasattr(n, "text")
            assert hasattr(n, "metadata")
            assert hasattr(n, "id_")
            assert len(n.text) > 0
            assert "section" in n.metadata
            assert "section_path" in n.metadata
            assert "token_count" in n.metadata

        # Verify debt table was kept intact in one node
        debt_found = any("Revolving Credit Facility" in n.text and "2029 Senior Secured Notes" in n.text for n in nodes)
        assert debt_found, "Debt schedule was not found intact in a single LlamaIndex TextNode"

    def test_get_nodes_from_documents(self, sample_pdf_paths):
        from llama_index.core.schema import Document as LlamaDoc
        _, leg_path = sample_pdf_paths

        # Test with a LlamaIndex document pointing to a PDF file on disk
        input_doc = LlamaDoc(text="Placeholder", metadata={"file_path": str(leg_path), "category": "legal_agreement"})
        parser = SDCANodeParser(target_tokens=300)
        nodes = parser.get_nodes_from_documents([input_doc])

        assert len(nodes) >= 3
        for n in nodes:
            assert n.metadata.get("category") == "legal_agreement"
            assert "section" in n.metadata

    def test_parse_in_memory_text(self):
        from llama_index.core.schema import Document as LlamaDoc
        raw_text = (
            "Article 1. Definitions\n\nAuthorized users means employees authorized to access services.\n\n"
            "Article 4. Fees\n\nInvoices are payable within 30 days."
        )
        input_doc = LlamaDoc(text=raw_text, metadata={"doc_type": "contract"})
        parser = SDCANodeParser(target_tokens=300)
        nodes = parser.get_nodes_from_documents([input_doc])

        assert len(nodes) >= 1
        assert nodes[0].metadata.get("doc_type") == "contract"
