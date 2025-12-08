import os
import pytest
from unittest.mock import patch, MagicMock

from src.fetcher import PDFFetcher  # adjust if your folder structure is different

# ----------------------------
# 1️⃣ Test: Initialization
# ----------------------------
def test_initialization():
    fetcher = PDFFetcher(pdf_file="my.pdf", hash_file="my.hash", keyword="test", page_url="http://example.com")
    assert fetcher.pdf_file == "my.pdf"
    assert fetcher.hash_file == "my.hash"
    assert fetcher.keyword == "test"
    assert fetcher.page_url == "http://example.com"
    assert fetcher.pdf_url is None
    assert fetcher.text is None

# ----------------------------
# 2️⃣ Test: get_pdf_url
# ----------------------------
@patch("src.fetcher.requests.get")
def test_get_pdf_url(mock_get):
    # Mock the HTTP response
    html = """
    <html><body>
        <h1>Test</h1>
        <div class="fl-rich-text">
            <a href="schedule.pdf">Click Here</a>
        </div>
    </body></html>
    """
    mock_response = MagicMock()
    mock_response.text = html
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    fetcher = PDFFetcher(keyword="test", page_url="http://example.com")
    url = fetcher.get_pdf_url()

    # Check if it returned the correct URL
    assert url == "http://example.com/schedule.pdf"
    assert fetcher.pdf_url == "http://example.com/schedule.pdf"

# ----------------------------
# 3️⃣ Test: download_pdf (mocking requests)
# ----------------------------
@patch("src.fetcher.requests.get")
@patch("builtins.open")
@patch("os.path.exists")
def test_download_pdf(mock_exists, mock_open, mock_get):
    # Pretend the PDF hash file exists
    mock_exists.return_value = False

    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.content = b"PDF content"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    fetcher = PDFFetcher(pdf_file="my.pdf", hash_file="my.hash")
    fetcher.pdf_url = "http://example.com/schedule.pdf"
    result = fetcher.download_pdf()

    # It should return True (new download)
    assert result is True

# ----------------------------
# 4️⃣ Test: fetch (integration test with mocks)
# ----------------------------
@patch.object(PDFFetcher, "get_pdf_url")
@patch.object(PDFFetcher, "download_pdf")
@patch.object(PDFFetcher, "extract_text")
def test_fetch(mock_extract, mock_download, mock_get_url):
    # Setup return values
    mock_download.return_value = True
    fetcher = PDFFetcher()
    result = fetcher.fetch()
    assert result is True
    mock_get_url.assert_called_once()
    mock_download.assert_called_once()
    mock_extract.assert_called_once()
