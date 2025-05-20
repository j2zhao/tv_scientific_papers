import random
import pandas as pd

def sample_sub_categories(df:pd.DataFrame, n:int):
    unique_pairs = df[['Category', 'Subcategory']].drop_duplicates()
    random_pairs = unique_pairs.sample(n=n, random_state=42)
    return random_pairs



