import pandas as pd
import numpy as np
import random
import math
import sys

input_filename = sys.argv[1]
amount_to_nullify = float(sys.argv[2])
columns_to_nullify = sys.argv[3:]
df = pd.read_csv(input_filename + '.csv', encoding='latin_1')
threshold = math.floor(len(df.index) * amount_to_nullify)

counter = 0

for row in df.index:
    for col in columns_to_nullify:
        value = random.randint(0, len(df.index)-1)
        if value < threshold:
            df.loc[row, col] = float('nan')
            counter += 1

ratio = counter / (len(df.index) * len(columns_to_nullify))
print('Amount nullified:', ratio)

output_filename = input_filename + '-nullified.csv'

df.to_csv(output_filename, index=False)