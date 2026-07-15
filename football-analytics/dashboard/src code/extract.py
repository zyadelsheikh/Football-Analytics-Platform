
"""
Data Extraction Layer:
Loads raw football datasets from CSV files
"""

import pandas as pd
from pathlib import Path


RAW_DIR = Path(
    r"C:\Users\3D STORE\Documents\depi\raw data"
)


def extract_data():
    """
    Read raw football datasets from CSV files.
    """

    df1 = pd.read_csv(
        RAW_DIR / "Top5_League_Players_2017to2024_dataset.csv",
        sep=";",
        decimal=","
    )

    df2 = pd.read_csv(
        RAW_DIR / "players_data-2025_2026.csv",
        decimal=","
    )

    return df1, df2