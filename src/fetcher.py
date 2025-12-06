import os
import re
import hashlib
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pdfplumber

from config import PAGE_URL, PDF_PATH, HASH_PATH, HEADERS
from utils import log

class PDFFetcher():

    def __init__(self, pdf_path=PDF_PATH, hash_path=HASH_PATH, keyword = KEYWORD, page_url=PAGE_URL):
        self.pdf_path = pdf_path
        self.hash_path = hash_path
        self.keyword = keyword
        self.page_url = page_url
        self.headers = HEADERS

    def get_pdf_url(self):
        pass  

    def download_pdf(self):
        pass

    def has_changed(self):
        pass

    def extract_text(self):
        pass

    
