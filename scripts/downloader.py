import os
import requests
from tqdm import tqdm

# Verified working URLs from indiacode.nic.in (India's official government code portal)
ACTS = {
    "consumer_protection_act_2019.pdf": "https://www.indiacode.nic.in/bitstream/123456789/16939/1/a2019-35.pdf",
    "rti_act_2005.pdf":                 "https://www.indiacode.nic.in/bitstream/123456789/2065/1/aa2005.pdf",
    "ipc_1860.pdf":                     "https://www.indiacode.nic.in/bitstream/123456789/11091/1/the_indian_penal_code,_1860.pdf",
    "crpc_1973.pdf":                    "https://www.indiacode.nic.in/bitstream/123456789/4221/1/Criminal-Procedure-Code-CrPC-1973.pdf",
}

SAVE_DIR = "data/raw/acts"
os.makedirs(SAVE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/pdf,*/*",
}

def download_file(url: str, filepath: str):
    response = requests.get(url, stream=True, timeout=60, headers=HEADERS)
    print(f"  Status      : {response.status_code}")
    print(f"  Content-Type: {response.headers.get('content-type', 'unknown')}")
    response.raise_for_status()

    total = int(response.headers.get("content-length", 0))
    with open(filepath, "wb") as f, tqdm(
        desc=os.path.basename(filepath),
        total=total, unit="B", unit_scale=True,
    ) as bar:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            bar.update(len(chunk))

if __name__ == "__main__":
    for filename, url in ACTS.items():
        filepath = os.path.join(SAVE_DIR, filename)

        # Skip if already a valid PDF (>50KB)
        if os.path.exists(filepath) and os.path.getsize(filepath) > 50_000:
            print(f"Already downloaded: {filename}")
            continue

        print(f"\nDownloading: {filename}")
        print(f"  URL: {url}")
        try:
            download_file(url, filepath)
            size_kb = os.path.getsize(filepath) // 1024
            print(f"  Saved: {size_kb} KB")
        except Exception as e:
            print(f"  FAILED: {e}")

    # Summary
    print("\n── Summary ─────────────────────────────")
    for filename in ACTS:
        path = os.path.join(SAVE_DIR, filename)
        if os.path.exists(path):
            size_kb = os.path.getsize(path) // 1024
            status = "OK" if size_kb > 50 else "TOO SMALL — likely an error page"
            print(f"  {status:<10} {filename} ({size_kb} KB)")
        else:
            print(f"  MISSING    {filename}")