from numpy import genfromtxt
import csv
import pandas as pd
import random
import math
import sys

file_name = sys.argv[1]
df = pd.read_csv(file_name, encoding="latin_1")

print(df.shape)
print(df)

data_len = len(df.index)
num_cols = 0
columns = sys.argv[3:] if len(sys.argv) > 3 else df.columns
num_cols = len(columns)

df = pd.read_csv(file_name, encoding="latin_1")
counter = 0

for i in range(0, data_len-1):
    for j in columns:
        value = random.randint(0,data_len-1)
        threshold = math.floor(data_len*float(sys.argv[2]))
        if value < threshold:
            rand_row = random.randint(0, data_len-1)
            df.at[i,j] = df.at[rand_row, j]
            counter += 1

ratio = counter/(data_len * num_cols)

print(df)
print("The number of updated values: ", counter)
print("The ratio of updated values: ", ratio)

export_csv = df.to_csv('dirty_' + sys.argv[1], encoding='utf-8', index=False, header=True)
