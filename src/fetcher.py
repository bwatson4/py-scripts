import os
import re
import hashlib
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pdfplumber

from config import PAGE_URL, PDF_FILE, PDF_HASH_FILE, HEADERS, KEYWORD
from utils import log

class PDFFetcher():

    def __init__(
        self, 
        pdf_file=PDF_FILE, 
        hash_file=PDF_HASH_FILE, 
        keyword = KEYWORD, 
        page_url=PAGE_URL
        ):
        self.pdf_file = pdf_file
        self.hash_file = hash_file
        self.keyword = keyword
        self.page_url = page_url
        self.headers = HEADERS
        self.pdf_url = None
        self.text = None

    def get_pdf_url(self):
        """
        Find the PDF URL associated with the given keyword on the page.
        Returns None if no matching PDF is found.
        """
        try:
            resp = requests.get(self.page_url, headers=self.headers)
            resp.raise_for_status()
        except requests.RequestException as e:
            log(f"Failed to fetch page: {e}")
            self.pdf_url = None
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # 1. Search for elements containing the keyword text
        keyword_elements = soup.find_all(string=re.compile(self.keyword, re.I))
        for element in keyword_elements:
            parent = element.parent

            # 2. Look for PDF links in parent
            pdf_links = [a for a in parent.find_all("a", href=True)
                        if a["href"].lower().endswith(".pdf")]
            if pdf_links:
                self.pdf_url = urljoin(self.page_url, pdf_links[0]["href"])
                return self.pdf_url

            # Optionally: check immediate siblings if needed
            for sibling in parent.find_next_siblings():
                pdf_links = [a for a in sibling.find_all("a", href=True)
                            if a["href"].lower().endswith(".pdf")]
                if pdf_links:
                    self.pdf_url = urljoin(self.page_url, pdf_links[0]["href"])
                    return self.pdf_url

        log(f"No PDF link found for keyword '{self.keyword}'.")
        self.pdf_url = None
        return None

    
    def download_pdf(self):
        """Downloads a new pdf, checks if it has changed.
        If it has changed: Save new hash and pdf in respective folder
        """
        #error handling if called in wrong order
        if not self.pdf_url:
            raise ValueError("PDF URL has not been set. Call get_pdf_url() first.")
        
        #get the pdf file and raise an error if fails
        resp = requests.get(self.pdf_url, headers=self.headers)
        resp.raise_for_status()

        # Compute hash of remote PDF (in memory)
        pdf_bytes = resp.content
        new_hash = hashlib.md5(pdf_bytes).hexdigest() 

        # get old hash and compare to new hash. Only save pdf if not matching
        old_hash = None
        if os.path.exists(self.hash_file):
            with open(self.hash_file, "r") as fh:
                old_hash = fh.read().strip()
        if new_hash == old_hash:
            return False
        
        with open(self.pdf_file, "wb") as fh:
            fh.write(resp.content)

        with open(self.hash_file, "w") as fh:
            fh.write(new_hash)
        return True

    def extract_text(self):
        self.text = ""
        with pdfplumber.open(self.pdf_file) as pdf:
            for page in pdf.pages:
                self.text += (page.extract_text() or "") + "\n"
        return self.text

    def fetch(self):
        self.get_pdf_url()
        changed = self.download_pdf()
        if changed:
            self.extract_text()
        return changed

