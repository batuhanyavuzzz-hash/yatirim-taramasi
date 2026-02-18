import pandas as pd

URL = "https://datahub.io/core/s-and-p-500-companies/r/constituents.csv"

df = pd.read_csv(URL)
out = pd.DataFrame({"ticker": df["Symbol"].astype(str).str.upper().str.strip()})
out.to_csv("universe_us.csv", index=False)

print("OK -> universe_us.csv written. rows:", len(out))
