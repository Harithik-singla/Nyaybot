import os
import time
import json
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

SAVE_DIR = "data/raw/kanoon"
os.makedirs(SAVE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Curated Indian Kanoon document IDs — real cases covering NyayBot's categories.
# Format: (doc_id, category, short_title)
CASE_IDS = [
    # Consumer protection
    ("1823221",  "consumer",    "Ghaziabad Development Authority vs Balbir Singh"),
    ("619152",   "consumer",    "Spring Meadows Hospital vs Harjol Ahluwalia"),
    ("1760576",  "consumer",    "Lucknow Development Authority vs M.K. Gupta"),
    ("257237",   "consumer",    "Indian Medical Association vs V.P. Shantha"),
    ("1194048",  "consumer",    "Charan Singh vs Healing Touch Hospital"),
    ("471959",   "consumer",    "M/s Emaar MGF vs Aftab Singh - Builder delay"),
    ("1922773",  "consumer",    "NCDRC insurance claim rejection"),

    # RTI Act
    ("1306872",  "rti",         "CBSE vs Aditya Bandopadhyay - RTI landmark"),
    ("1390872",  "rti",         "Girish Ramchandra Deshpande vs CIC - RTI scope"),
    ("169723",   "rti",         "Namit Sharma vs Union of India - RTI"),
    ("1113277",  "rti",         "Central Board of Secondary Education vs RTI"),
    ("872535",   "rti",         "Public Information Officer vs Subhash Chandra"),

    # Tenant / landlord
    ("1144958",  "tenancy",     "Saul Hameed vs Mohd Hussain - eviction"),
    ("1198958",  "tenancy",     "Shiv Sarup Gupta vs Dr Mahesh Chand Gupta"),
    ("490479",   "tenancy",     "Atma Ram Properties vs Federal Motors - rent"),
    ("1255438",  "tenancy",     "Smt Gian Devi vs Jeevan Kumar - tenancy rights"),

    # Employment / labour
    ("828950",   "employment",  "Workmen vs Meenakshi Mills - labour rights"),
    ("1376342",  "employment",  "Mahindra and Mahindra vs NJ Engineer - termination"),
    ("92812",    "employment",  "Air India vs Nargesh Mirza - employment rights"),
    ("1440546",  "employment",  "Hindustan Tin Works vs Employees - retrenchment"),

    # Police / FIR
    ("1233066",  "police_fir",  "Lalita Kumari vs Govt of UP - mandatory FIR"),
    ("1939993",  "police_fir",  "Arnesh Kumar vs State of Bihar - arrest guidelines"),
    ("1571538",  "police_fir",  "D.K. Basu vs State of West Bengal - arrest rights"),

    # Cheque bounce
    ("1086282",  "cheque",      "Dashrath Rupsingh Rathod vs State - cheque bounce"),
    ("1317835",  "cheque",      "Kusum Ingots vs Pennar Peterson - NI Act 138"),
    ("1200702",  "cheque",      "MSR Leathers vs S. Palaniappan - cheque dishonour"),

    # Motor accident / compensation
    ("1388660",  "motor",       "Sarla Verma vs Delhi Transport - compensation"),
    ("1356613",  "motor",       "National Insurance vs Pranay Sethi - motor claim"),
    ("1424442",  "motor",       "Raj Kumar vs Ajay Kumar - accident compensation"),

    # Property dispute
    ("1279834",  "property",    "Suraj Lamp vs State of Haryana - property transfer"),
    ("445767",   "property",    "Thakur Kishan Singh vs Arvind Kumar - possession"),
]

def fetch_case(doc_id: str) -> dict:
    """Fetch a single case document from Indian Kanoon."""
    url = f"https://indiankanoon.org/doc/{doc_id}/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        return {"error": str(e)}

    soup = BeautifulSoup(resp.text, "html.parser")

    # Get title
    title_tag = soup.find("h2", class_="doc_title") or soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else f"Case {doc_id}"

    # Get judgment text — inside div#judgments or div.judgments
    content = (
        soup.find("div", id="judgments") or
        soup.find("div", class_="judgments") or
        soup.find("div", id="doc_fragment")
    )

    if not content:
        # Fallback: grab all paragraph text
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30)
    else:
        text = content.get_text(separator="\n", strip=True)

    return {
        "doc_id": doc_id,
        "title": title,
        "url": url,
        "text": text,
        "word_count": len(text.split()),
    }

if __name__ == "__main__":
    print(f"Fetching {len(CASE_IDS)} cases from Indian Kanoon...")
    print("Sleeping 2s between requests to be polite.\n")

    results = []
    failed = []

    for doc_id, category, short_title in tqdm(CASE_IDS):
        case = fetch_case(doc_id)
        time.sleep(2)

        if "error" in case:
            print(f"  FAILED {doc_id} ({short_title}): {case['error']}")
            failed.append(doc_id)
            continue

        if case["word_count"] < 100:
            print(f"  TOO SHORT {doc_id} ({short_title}): {case['word_count']} words")
            failed.append(doc_id)
            continue

        case["category"] = category
        case["short_title"] = short_title
        results.append(case)
        print(f"  OK  {short_title[:50]:<50} {case['word_count']:>6} words")

    output_path = os.path.join(SAVE_DIR, "cases.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nDone: {len(results)} cases saved, {len(failed)} failed")
    print(f"Output: {output_path}")
    if failed:
        print(f"Failed IDs: {failed}")