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

def download_paper_pdf(paper_df: pd.DataFrame,
                       self_df: pd.DataFrame,
                       artifact_folder:str) -> None:

    for _, paper, in paper_df.iterrows():
        if paper['url'] is not None and paper['paperId'] not in self_df['paperId'].values:
            file_path = os.path.join(artifact_folder, paper['Category'], paper['Subcategory']) 
            os.makedirs(file_path)
            file_path = os.path.join(file_path, f'{paper['paperId']}.pdf')
            success = download_pdf(paper['url'], filepath = file_path)
            new_row = [paper['paperId'], paper['title'], success, file_path]
            self_df = pd.concat([self_df, new_row], ignore_index=True)
    return self_df