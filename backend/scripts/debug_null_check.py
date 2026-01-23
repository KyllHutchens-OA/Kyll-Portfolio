"""
Debug NULL check logic.
"""
import pandas as pd

# Simulate what we get from the database
data = pd.DataFrame({"average_disposals_2024": [None]})

print("DataFrame:")
print(data)
print(f"\nDataFrame length: {len(data)}")
print(f"\nIs NULL check: {data.isnull().all().all()}")
print(f"\nColumn-wise NULL: {data.isnull().all()}")
print(f"\nRow-wise NULL: {data.isnull().all(axis=1)}")

# Test the actual condition
all_null = data.isnull().all().all() if len(data) > 0 else False
print(f"\nall_null result: {all_null}")
