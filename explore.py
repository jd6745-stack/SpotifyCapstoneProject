import pandas as pd

# 1. Look at the first 100,000 rows
df = pd.read_csv("data/charts.csv", nrows=100_000)
print(df.head())   # first 5 rows
df.info()          # column names, data types, missing values

# 2. List every region in the whole file (reads only that one column, in pieces)
regions = set()
for chunk in pd.read_csv("data/charts.csv", usecols=["region"], chunksize=1_000_000):
    regions.update(chunk["region"].unique())
print(sorted(regions))
