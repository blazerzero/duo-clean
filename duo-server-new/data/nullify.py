import pandas as pd
import numpy as np
import random
import math
import sys

input_filename = sys.argv[1]
amount_to_nullify = float(sys.argv[2])
df = pd.read_csv(input_filename + '.csv', encoding='latin_1')
columns_to_nullify = sys.argv[3:] if len(sys.argv) > 2 else df.columns
threshold = math.floor(len(df.index) * amount_to_nullify)

counter = 0
print(df)

for row in df.index:
    for col in columns_to_nullify:
        value = random.randint(0, len(df.index)-1)
        tuple_contains_null = False
        for c in [co for co in columns_to_nullify if co != col]:
            if pd.isnull(df.at[row, c]):
                tuple_contains_null = True
        if tuple_contains_null == False and value < threshold:
            df.loc[row, col] = float('nan')
            counter += 1

ratio = counter / (len(df.index) * len(columns_to_nullify))
print('Amount nullified:', ratio)

output_filename = input_filename + '-nullified.csv'

df.to_csv(output_filename, index=False)