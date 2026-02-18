import pandas as pd

class DataProvider:
    def history(self, ticker: str, start, end) -> pd.DataFrame:
        raise NotImplementedError
