"""Unit tests for Multi-Domain Document Processing (Financial 10-K & Legal Contracts)."""

from pathlib import Path
import pytest

from scripts.eval_multi_domain import (
    FINANCIAL_QUERIES,
    LEGAL_QUERIES,
    check_heading_detachment,
    check_section_context_retention,
    check_table_preservation_10k,
    run_retrieval_benchmark,
)
from src.extraction.pdf_parser import load_pdf
from src.sdca.v3.chunker import chunk_sdca_stair


@pytest.fixture(scope="module")
def multi_domain_paths():
    base = Path("data/multi_domain")
    fin = base / "financial_10k_sample.pdf"
    leg = base / "commercial_contract_sample.pdf"
    assert fin.exists(), f"Missing {fin}"
    assert leg.exists(), f"Missing {leg}"
    return fin, leg


def test_financial_10k_table_preservation(multi_domain_paths):
    fin_path, _ = multi_domain_paths
    doc = load_pdf(fin_path)
    chunks = chunk_sdca_stair(doc, target_tokens=300)

    res = check_table_preservation_10k(chunks)
    assert res["preservation_rate"] == 1.0, f"Expected 100% table preservation, got {res}"
    assert res["preserved_count"] == 3


def test_financial_10k_heading_detachment(multi_domain_paths):
    fin_path, _ = multi_domain_paths
    doc = load_pdf(fin_path)
    chunks = chunk_sdca_stair(doc, target_tokens=300)

    detach_res = check_heading_detachment(chunks)
    assert detach_res["detached_count"] == 0, f"Expected 0 detached headings, got {detach_res}"


def test_legal_contract_section_retention(multi_domain_paths):
    _, leg_path = multi_domain_paths
    doc = load_pdf(leg_path)
    chunks = chunk_sdca_stair(doc, target_tokens=300)

    retention = check_section_context_retention(chunks)
    assert retention == 1.0, f"Expected 100% section retention, got {retention}"


def test_legal_contract_zero_heading_detachment(multi_domain_paths):
    _, leg_path = multi_domain_paths
    doc = load_pdf(leg_path)
    chunks = chunk_sdca_stair(doc, target_tokens=300)

    detach_res = check_heading_detachment(chunks)
    assert detach_res["detached_count"] == 0


def test_multi_domain_retrieval_smoke(multi_domain_paths):
    fin_path, leg_path = multi_domain_paths
    fin_results = run_retrieval_benchmark(fin_path, FINANCIAL_QUERIES, chunk_sdca_stair, "SDCA (STAIR)")
    leg_results = run_retrieval_benchmark(leg_path, LEGAL_QUERIES, chunk_sdca_stair, "SDCA (STAIR)")

    assert len(fin_results) == len(FINANCIAL_QUERIES)
    assert len(leg_results) == len(LEGAL_QUERIES)

    # Verify at least 75% accuracy
    fin_hits = sum(1 for r in fin_results if r["full_keyword_hit"])
    leg_hits = sum(1 for r in leg_results if r["full_keyword_hit"])
    assert fin_hits >= 3
    assert leg_hits >= 3
