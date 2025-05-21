

import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import time
from typing import Optional
import sys
import os
import pandas as pd

import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def fetch_papers(params, api_key=None, max_papers=None, max_retries=10, backoff_factor=2):
    """
    Fetch papers from the Semantic Scholar API with retry mechanism and pagination support.
    
    The bulk search endpoint returns up to 1,000 papers per call and provides a continuation
    token if more results are available. This function will repeatedly fetch batches of papers
    until either no further token is provided or the desired number of papers (max_papers) is reached.
    
    Args:
        params (dict): Query parameters for the API request.
            At minimum, the 'query' parameter is required.
        api_key (str, optional): API key for authentication. Defaults to None.
        max_papers (int, optional): Maximum number of papers to fetch. If None, fetches all available papers.
        max_retries (int, optional): Maximum number of retry attempts per API call. Defaults to 3.
        backoff_factor (int, optional): Factor for exponential backoff between retries. Defaults to 2.
    
    Returns:
        list: A list of paper records if successful, otherwise an empty list.
    """
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
    headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }


    if api_key:
        headers['x-api-key'] = api_key

    # Set up a session with a retry strategy
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    papers = []
    token = None 

    while True:
        request_params = params.copy()
        if token:
            request_params['token'] = token

        try:
            response = session.get(base_url, params=request_params, headers=headers)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed after {max_retries} retries: {e}")
            break

        if 'data' not in data or not data['data']:
            print("'data' key is missing or empty in the response.")
            break
        papers.extend(data['data'])
        if max_papers is not None and len(papers) >= max_papers:
            papers = papers[:max_papers]
            break
        token = data.get('token')
        if not token:
            break
        time.sleep(1)

    return papers

def get_all_papers_in_journals(journals:list[tuple[str, str]],
                               year:Optional[int],
                               max_per_journal:Optional[int],
                               semantic_key:Optional[str]) -> None:
    all_papers = []
    for jname, cleaned_jname in journals:
        params = {'query': '', 
                "fields": "title,year,url,isOpenAccess,openAccessPdf,venue,publicationTypes", 
                'venue':jname,
                'publicationTypes':'Review,JournalArticle,CaseReport,ClinicalTrial,Conference,Dataset,MetaAnalysis,Study,Book,BookSection'}
        if year is None:
            year = [None]
        
        if year:
            params['year'] = year
        papers = fetch_papers(params, api_key=semantic_key, max_papers=max_per_journal)
        for paper in papers:
            if paper['isOpenAccess'] and paper['openAccessPdf'] is not None:
                open_access_url = paper['openAccessPdf']['url']
            else:
                open_access_url = ""
            all_papers.append((paper['paperId'], paper['title'], cleaned_jname, open_access_url,  paper['year'], paper['publicationTypes']))
        time.sleep(1)
    df = pd.DataFrame(all_papers, columns=['paperId', 'title', 'journal', 'url', 'year', 'type'])
    return df

def papers_from_sub_category(selected_categories:pd.DataFrame, 
                 all_journals:pd.DataFrame, 
                 years:Optional[list[int]], 
                 max_per_journal:Optional[int],
                 semantic_key:Optional[str]):
    if years is None:
        years = [None]

    all_papers = []
    for _, row in selected_categories.iterrows():
        category = row['Category_cleaned']
        subcategory = row['Subcategory_cleaned']
        for year in years:
            # if year is None:
            #     cat_folder = f'{category}_{subcategory}'
            # else:
            #     cat_folder = f'{category}_{subcategory}_{year}'
            # paper_path = os.path.join('..','paper_repository', 'paper_by_field', cat_folder)
            # os.makedirs(paper_path, exist_ok=True)
            # paper_path = os.path.join(paper_path, 'papers_info.csv')
            journals = all_journals[(all_journals["Category_cleaned"] == category) & (all_journals["Subcategory_cleaned"] == subcategory)]
            journals_list = list(journals[['Journal', 'Journal_cleaned']].itertuples(index=False, name=None))
            df = get_all_papers_in_journals(journals_list, year, max_per_journal, semantic_key)
            df["Category_cleaned"] = category
            df["Subcategory_cleaned"] = subcategory
            all_papers.append(df)
    all_papers = pd.concat(all_papers, axis=1, ignore_index=True)
    return all_papers