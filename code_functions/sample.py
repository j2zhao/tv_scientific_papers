import random
import pandas as pd

def sample_sub_categories(df:pd.DataFrame, n:int):
    unique_pairs = df["Subcategory_cleaned","Category_cleaned"].drop_duplicates()
    random_pairs = unique_pairs.sample(n=n, random_state=42)
    return random_pairs

def gen_valid_paperids(df:pd.DataFrame, 
                       id_column:str, 
                       selection_column:str):
    df_ = df[df[selection_column]][[id_column]]
    return df_
