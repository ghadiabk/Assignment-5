import pandas as pd
import numpy as np

def clean_ebay_data(input_file='ebay_tech_deals.csv', output_file='cleaned_ebay_deals.csv'):
    df = pd.read_csv(input_file, dtype=str)

    df = df.loc[:, df.columns.notnull()]
    df = df.drop(columns=[col for col in df.columns if col.strip() == '' or 'Unnamed' in col], errors='ignore')

    if 'title' in df.columns:
        df['title'] = df['title'].astype(str).str.strip()
        df = df[df['title'].notna() & (df['title'] != '') & (df['title'].str.lower() != 'nan')]
    else:
        print("'title' column not found")

    for col in ['price', 'original_price']:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r'(?i)US', '', regex=True)
                .str.replace(r'\$', '', regex=True)
                .str.replace(',', '', regex=True)
                .str.replace(r'\n.*', '', regex=True)
                .str.replace(r'[^\d\.]', '', regex=True)
                .str.strip()
            )
        else:
            df[col] = np.nan

    df['original_price'] = df['original_price'].replace(['N/A', '', ' '], np.nan)
    df['original_price'] = df['original_price'].fillna(df['price'])

    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['original_price'] = pd.to_numeric(df['original_price'], errors='coerce')

    df['price'] = df['price'].fillna(df['original_price'])

    if 'shipping' in df.columns:
        df['shipping'] = df['shipping'].replace(['N/A', '', ' '], np.nan)
        df['shipping'] = df['shipping'].fillna("Shipping info unavailable")
    else:
        df['shipping'] = "Shipping info unavailable"

    df['discount_percentage'] = np.where(
        (df['original_price'] > 0) & (df['price'].notnull()),
        ((df['original_price'] - df['price']) / df['original_price']) * 100,
        np.nan
    ).round(2)

    df = df.drop_duplicates(subset=["title", "price", "original_price", "discount_percentage"])

    df.to_csv(output_file, index=False)
    print(df.head())

if __name__ == "__main__":
    clean_ebay_data()