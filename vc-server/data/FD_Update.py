from numpy import genfromtxt
import csv
import pandas as pd
import random
import math
import sys

file_name = sys.argv[1] + '-clean.csv'
df = pd.read_csv(file_name, encoding="latin_1")

print(df.shape)
print(df)

counter5 = 0
data_len = len(df.index)
num_cols = 0
columns = sys.argv[2:] if len(sys.argv) > 2 else df.columns
num_cols = len(columns)

for i in range(0, data_len-1):
    for j in columns:
        value = random.randint(0,data_len-1)
        threshold = math.floor(data_len*0.05)
        if value < threshold:
            df.at[i,j] = df.at[i+1, j]
            counter5 += 1

ratio5 = counter5/(data_len * num_cols)

print(df)
print("The number of updated values with 5% noise: ", counter5)
print("The ratio of updated values with 5% noise: ", ratio5)

export_csv = df.to_csv(sys.argv[1] + '-dirty_05.csv', encoding='utf-8', index=False, header=True)

df = pd.read_csv(file_name, encoding="latin_1")
counter10 = 0

for i in range(0, data_len-1):
    for j in columns:
        value = random.randint(0,data_len-1)
        threshold = math.floor(data_len*0.1)
        if value < threshold:
            df.at[i,j] = df.at[i+1, j]
            counter10 += 1

ratio10 = counter10/(data_len * num_cols)

print(df)
print("The number of updated values with 10% noise: ", counter10)
print("The ratio of updated values with 10% noise: ", ratio10)

export_csv = df.to_csv(sys.argv[1] + '-dirty_10.csv', encoding='utf-8', index=False, header=True)

df = pd.read_csv(file_name, encoding="latin_1")
counter20 = 0

for i in range(0, data_len-1):
    for j in columns:
        value = random.randint(0,data_len-1)
        threshold = math.floor(data_len*0.2)
        if value < threshold:
            df.at[i,j] = df.at[i+1, j]
            counter20 += 1

ratio20 = counter20/(data_len * num_cols)

print(df)
print("The number of updated values with 20% noise: ", counter20)
print("The ratio of updated values with 20% noise: ", ratio20)

export_csv = df.to_csv(sys.argv[1] + '-dirty_20.csv', encoding='utf-8', index=False, header=True)

df = pd.read_csv(file_name, encoding="latin_1")
counter25 = 0

for i in range(0, data_len-1):
    for j in columns:
        value = random.randint(0,data_len-1)
        threshold = math.floor(data_len*0.25)
        if value < threshold:
            df.at[i,j] = df.at[i+1, j]
            counter25 += 1

ratio25 = counter25/(data_len * num_cols)

print(df)
print("The number of updated values with 25% noise: ", counter25)
print("The ratio of updated values with 25% noise: ", ratio25)

export_csv = df.to_csv(sys.argv[1] + '-dirty_25.csv', encoding='utf-8', index=False, header=True)

df = pd.read_csv(file_name, encoding="latin_1")
counter30 = 0

for i in range(0, data_len-1):
    for j in columns:
        value = random.randint(0,data_len-1)
        threshold = math.floor(data_len*0.3)
        if value < threshold:
            df.at[i,j] = df.at[i+1, j]
            counter30 += 1

ratio30 = counter30/(data_len * num_cols)

print(df)
print("The number of updated values with 30% noise: ", counter30)
print("The ratio of updated values with 30% noise: ", ratio30)

export_csv = df.to_csv(sys.argv[1] + '-dirty_30.csv', encoding='utf-8', index=False, header=True)
