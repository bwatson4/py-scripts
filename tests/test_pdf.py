# test_pdf.py
# from check_schedule import download_pdf, extract_text, parse_schedule

# download_pdf()

# text = extract_text()
# with open("schedule_debug.txt", "w", encoding="utf-8") as f:
#     f.write(text)

# events = parse_schedule(text)

# print(f"Found {len(events)} events:")
# for e in events:
#     print(f"{e['summary']} | {e['description']} | {e['start']} - {e['end']}")


import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0.0.0 Safari/537.36"
    )
}

def find_schedule_pdfs(page_url, filter_keywords=None):
    """
    Fetches the page at `page_url`, finds all .pdf links,
    and returns a list of absolute URLs to those PDFs.
    Optionally filters the results by keywords (in the URL or link text).

    Args:
        page_url (str): The URL of the page listing the schedule(s).
        filter_keywords (list of str, optional): if provided, only PDFs whose
            URL or surrounding link text contains any of these (case-insensitive)
            strings will be returned.

    Returns:
        list of str: full URLs to the matched PDF files.
    """
    resp = requests.get(page_url, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    pdf_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # check if link ends with .pdf (case-insensitive)
        if href.lower().endswith(".pdf"):
            full_url = urljoin(page_url, href)
            # if filter_keywords specified, check if any keyword appears
            if filter_keywords:
                text = (a.get_text() or "") + " " + href
                text = text.lower()
                if not any(kw.lower() in text for kw in filter_keywords):
                    continue
            pdf_links.append(full_url)

    return pdf_links

if __name__ == "__main__":
    url = "https://kvapack.ca/adult-indoor/"
    # e.g. to try to get Wednesday PDFs:
    wednesday_pdfs = find_schedule_pdfs(url)
    print("Found PDFs:")
    for pdf in wednesday_pdfs:
        print(f"{pdf}")