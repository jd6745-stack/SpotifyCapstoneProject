import pandas as pd

# The 15 regions in our subset
REGIONS = [
    "Global", "United States", "United Kingdom", "Canada", "Australia",
    "Brazil", "Mexico", "Argentina", "Germany", "France",
    "Spain", "Italy", "Netherlands", "Sweden", "Japan",
]

parts = []
for chunk in pd.read_csv("data/charts.csv", chunksize=1_000_000):
    chunk = chunk[
        (chunk["chart"] == "top200")
        & (chunk["rank"] <= 100)
        & (chunk["date"] >= "2019-01-01")
        & (chunk["date"] <= "2020-12-31")
        & (chunk["region"].isin(REGIONS))
    ]
    parts.append(chunk)

subset = pd.concat(parts, ignore_index=True)
print(len(subset), "rows in the subset")
subset.to_csv("data/charts_subset.csv", index=False)
