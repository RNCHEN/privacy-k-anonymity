import pandas as pd
import numpy as np
from collections import Counter

# Load dataset (update 'dataset.csv' to actual filename)
file_path = r"D:\25spring\privacy\projext\code\untitled3\COVID-19_Treatments_20250203.csv"
df = pd.read_csv(file_path)

# Define quasi-identifiers (QIs) - based on dataset structure
quasi_identifiers = ["city", "state_code", "zip", "county"]  # Adjust as needed

# Create equivalence classes based on QIs
df["eq_class"] = df[quasi_identifiers].apply(lambda row: tuple(row), axis=1)

# Count occurrences of each equivalence class
eq_class_counts = Counter(df["eq_class"])

# Compute K for each record
df["k_value"] = df["eq_class"].map(eq_class_counts)

# Compute K-Anonymity Metrics
total_records = len(df)
num_eq_classes = len(eq_class_counts)
AECS = total_records / num_eq_classes  # Average Equivalence Class Size
ECSV = np.var(list(eq_class_counts.values()))  # Variance in Equivalence Class Size
suppression_rate = sum(df["k_value"] == 1) / total_records  # Records appearing only once

# Display Results
print(f"Total Records: {total_records}")
print(f"Number of Equivalence Classes: {num_eq_classes}")
print(f"K-Anonymity Level (Min K in dataset): {min(df['k_value'])}")
print(f"AECS (Avg Equivalence Class Size): {AECS:.2f}")
print(f"ECSV (Variance in Equivalence Class Size): {ECSV:.2f}")
print(f"Suppression Rate: {suppression_rate:.2%}")

# Output equivalence class distribution
df[["eq_class", "k_value"]].drop_duplicates().sort_values("k_value", ascending=True).head(20)
