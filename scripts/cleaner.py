import os
import re
import json
import pdfplumber
from tqdm import tqdm

RAW_ACTS_DIR = "data/raw/acts"
RAW_KANOON_PATH = "data/raw/kanoon/cases.json"
CLEAN_DIR = "data/clean"
os.makedirs(CLEAN_DIR, exist_ok=True)

# ── PDF cleaning ──────────────────────────────────────────────────────────────

def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from a PDF using pdfplumber."""
    text_pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in tqdm(pdf.pages, desc=f"  Pages in {os.path.basename(pdf_path)}", leave=False):
            text = page.extract_text()
            if text:
                text_pages.append(text)
    return "\n".join(text_pages)

def clean_legal_text(text: str) -> str:
    """
    Remove common boilerplate patterns from Indian legal documents.
    This is the most important cleaning step — bad cleaning = bad retrieval.
    """
    # Remove page numbers (standalone digits on a line)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)

    # Remove repeated headers/footers (lines that repeat 3+ times)
    lines = text.split("\n")
    line_counts: dict[str, int] = {}
    for line in lines:
        stripped = line.strip()
        if len(stripped) > 10:
            line_counts[stripped] = line_counts.get(stripped, 0) + 1

    boilerplate = {line for line, count in line_counts.items() if count >= 3}
    lines = [l for l in lines if l.strip() not in boilerplate]
    text = "\n".join(lines)

    # Collapse multiple blank lines into one
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove non-printable characters
    text = re.sub(r"[^\x20-\x7E\n\u0900-\u097F]", " ", text)

    # Collapse multiple spaces
    text = re.sub(r" {2,}", " ", text)

    return text.strip()

def process_acts():
    print("\nProcessing bare acts PDFs...")
    for filename in os.listdir(RAW_ACTS_DIR):
        if not filename.endswith(".pdf"):
            continue

        pdf_path = os.path.join(RAW_ACTS_DIR, filename)
        out_name = filename.replace(".pdf", ".txt")
        out_path = os.path.join(CLEAN_DIR, out_name)

        if os.path.exists(out_path):
            print(f"  Already cleaned: {out_name}")
            continue

        print(f"  Extracting: {filename}")
        raw_text = extract_pdf_text(pdf_path)
        clean_text = clean_legal_text(raw_text)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(clean_text)

        word_count = len(clean_text.split())
        print(f"  Saved: {out_name} ({word_count:,} words)")

# ── Kanoon case cleaning ──────────────────────────────────────────────────────

def clean_case_text(text: str) -> str:
    """Clean scraped case text."""
    # Remove URLs
    text = re.sub(r"http\S+", "", text)

    # Remove citation noise like [1990] 2 SCC 100
    text = re.sub(r"\[\d{4}\]\s+\d+\s+\w+\s+\d+", "", text)

    # Remove excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    return text.strip()

def process_kanoon_cases():
    print("\nProcessing Indian Kanoon cases...")

    if not os.path.exists(RAW_KANOON_PATH):
        print(f"  Not found: {RAW_KANOON_PATH} — run scraper.py first")
        return

    with open(RAW_KANOON_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    clean_cases = []
    skipped = 0

    for case in tqdm(cases, desc="  Cleaning cases"):
        raw_text = case.get("full_text", "")
        clean_text = clean_case_text(raw_text)

        # Skip cases with very little content
        if len(clean_text.split()) < 100:
            skipped += 1
            continue

        clean_cases.append({
            "title": case["title"],
            "url": case["url"],
            "query_category": case["query"],
            "text": clean_text,
            "word_count": len(clean_text.split()),
        })

    out_path = os.path.join(CLEAN_DIR, "kanoon_cases.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(clean_cases, f, ensure_ascii=False, indent=2)

    print(f"  Cleaned {len(clean_cases)} cases (skipped {skipped} too-short entries)")
    print(f"  Saved → {out_path}")

# ── Summary ───────────────────────────────────────────────────────────────────

def print_corpus_summary():
    print("\n── Corpus summary ──────────────────────────────")

    total_words = 0

    for filename in os.listdir(CLEAN_DIR):
        filepath = os.path.join(CLEAN_DIR, filename)

        if filename.endswith(".txt"):
            with open(filepath, "r", encoding="utf-8") as f:
                words = len(f.read().split())
            print(f"  {filename:<45} {words:>8,} words")
            total_words += words

        elif filename == "kanoon_cases.json":
            with open(filepath, "r", encoding="utf-8") as f:
                cases = json.load(f)
            words = sum(c["word_count"] for c in cases)
            print(f"  kanoon_cases.json ({len(cases)} cases){'':<18} {words:>8,} words")
            total_words += words

    print(f"  {'─'*52}")
    print(f"  {'TOTAL':<45} {total_words:>8,} words")
    print()

if __name__ == "__main__":
    process_acts()
    process_kanoon_cases()
    print_corpus_summary()