import pandas as pd
import os
import requests

def is_pdf(filepath: str) -> bool:
    try:
        with open(filepath, 'rb') as f:
            header = f.read(4)
            return header == b'%PDF'
    except IOError as e:
        return False


def download_pdf(url: str, filepath: str, timeout: int = 30) -> bool:
    try:        
        with requests.get(url, stream=True, timeout=timeout) as response:
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            # Check if the Content-Type is PDF
            content_type = response.headers.get('Content-Type', '').lower()
            if 'application/pdf' not in content_type:
                return False
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)

        if not is_pdf(filepath):
            os.remove(filepath)  # Remove the invalid file
            return False
        return True
    except Exception as e:
        return False

def download_paper_pdf(paper_id:str,
                       paper_url: str,
                       category: str,
                       subcategory:str,
                       artifact_folder:str) -> None:
    if paper_url is None or paper_url == "":
        return False, ""
    file_path = os.path.join(artifact_folder, category, subcategory) 
    os.makedirs(file_path)
    file_path = os.path.join(file_path, f'{paper_id}.pdf')
    success = download_pdf(paper_url, filepath = file_path)
    if not success:
        file_path == ""
    return success, file_path