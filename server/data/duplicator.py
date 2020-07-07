from numpy import genfromtxt
import csv
import pandas as pd
import random
import math
import sys

file_name = sys.argv[1]
df = pd.read_csv(file_name, encoding="latin_1")

counter = 0
data_len = len(df.index)
dup_level = float(sys.argv[2])

for i in range(0, data_len-1):
    rand_row = random.randint(0, data_len-1)
    value = random.randint(0,data_len-1)
    threshold = math.floor(data_len*dup_level)
    if value < threshold:
        for j in df.columns:
                df.at[i,j] = df.at[rand_row, j]
                counter += 1

export_csv = df.to_csv('out.csv', encoding='utf-8', index=False, header=True)

