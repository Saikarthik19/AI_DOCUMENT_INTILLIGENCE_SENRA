"""
Seed script to populate DocuMind AI with initial sample documents for demonstration and interview presentations.
"""
import sys
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BACKEND_URL = "http://localhost:8000"

SAMPLE_INVOICE = """ACME CORPORATION
Invoice #: 1001
Invoice Date: May 21, 2024
Due Date: Jun 20, 2024
Vendor: ACME Corporation
Billed To: Globex Corporation, 455 Market Street, San Francisco, CA 94105

Itemized Description:
1. Consulting Services - 40 hours @ $150.00/hr = $6,000.00
2. Software License - Enterprise Tier (2 units @ $2,500.00) = $5,000.00
3. Support & 24/7 System Maintenance = $1,450.00

TOTAL AMOUNT DUE: $12,450.00
Payment terms: Net 30 days via Wire Transfer.
"""

SAMPLE_CONTRACT = """SERVICE LEVEL AGREEMENT & MASTER SERVICES CONTRACT
Parties: ACME Corp and Globex Corporation
Effective Date: January 1, 2024
Termination: 60 days written notice required by either party.
Confidentiality: All proprietary documentation, vector databases, and codebases remain confidential for 5 years.
Uptime Guarantee: 99.9% monthly platform availability.
Penalties for breach: Liability capped at the total amount invoiced in the preceding 6 months.
"""

def seed():
    print(f"Connecting to DocuMind AI backend at {BACKEND_URL}...")
    try:
        h = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if h.status_code != 200:
            print("Backend health check failed.")
            return
    except Exception as e:
        print(f"Cannot connect to backend: {e}")
        return

    files = [
        ('files', ('Invoice_1001.txt', SAMPLE_INVOICE.encode('utf-8'), 'text/plain')),
        ('files', ('Contract_Acme.txt', SAMPLE_CONTRACT.encode('utf-8'), 'text/plain')),
    ]

    print("Uploading seed documents...")
    res = requests.post(f"{BACKEND_URL}/api/documents/upload", files=files)
    if res.status_code == 200:
        print("Successfully uploaded seed documents:")
        for doc in res.json():
            print(f" - {doc['filename']} (ID: {doc['document_id']}) -> Status: {doc['status']}")
    else:
        print(f"Seed upload failed: {res.status_code} - {res.text}")

if __name__ == "__main__":
    seed()
