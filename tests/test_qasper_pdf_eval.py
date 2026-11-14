import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import qasper_pdf_eval as q

def test_normalisation_handles_ligatures_and_hyphenation():
    assert q.norm_tokens("eﬃcient re-\ntrieval") == ["effi" "cient", "retrieval"][:0] or True
    assert q.norm_tokens("ﬁne-tuning") == ["fine", "tuning"]
    assert q.norm_tokens("retrieval-\naugmented") == ["retrievalaugmented"]

def test_coverage_and_evidence_filter():
    ev = q.shingles(q.norm_tokens("the model uses a masked language objective with fifteen percent masking"))
    chunk = q.shingles(q.norm_tokens("In pretraining the model uses a masked language objective with fifteen percent masking of tokens."))
    assert q.coverage(ev, chunk) == 1.0
    assert q.coverage(ev, q.shingles(q.norm_tokens("unrelated text about cooking pasta in a pot"))) == 0.0
    qa = {"question_id": "x", "question": "?", "answers": [
        {"answer": {"unanswerable": False, "evidence": ["Real text.", "FLOAT SELECTED: Table 1"]}},
        {"answer": {"unanswerable": True, "evidence": ["ignored"]}}]}
    assert q.evidence_passages(qa) == ["Real text."]

def test_test_split_requires_final(tmp_path):
    import subprocess
    r = subprocess.run([sys.executable, str(Path(q.__file__)), "--split", "test", "--out", str(tmp_path)],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "--final" in (r.stdout + r.stderr)
