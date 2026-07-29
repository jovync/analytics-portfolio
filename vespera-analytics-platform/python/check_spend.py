import pandas as pd

df = pd.read_csv("../data/raw/marketing_spend.csv")

print(df.groupby("channel")["spend_sgd"].sum().sort_values(ascending=False))
print()
print(f"Total: SGD {df['spend_sgd'].sum():,.2f}")