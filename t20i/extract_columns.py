import pandas as pd

df = pd.read_csv("t20.csv")
df_subset = df[['url', 'series_name']]
df_subset.to_csv("t20_url_series.csv", index=False)
print(f"Extracted {len(df_subset)} rows with url and series_name columns")