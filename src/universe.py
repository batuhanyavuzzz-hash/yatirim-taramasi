import pandas as pd

def load_universe():
    df = pd.read_csv("universe_us.csv")
    col = df.columns[0]
    return df[col].astype(str).str.upper().tolist()
