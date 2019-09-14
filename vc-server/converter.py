import csv
import sys
from tqdm import tqdm

def txt2csv(fn):
    #fnPieces = fn.split("/")
    fnFront = fn.split(".")[0]

    in_txt = csv.reader(open(fn, 'r'), delimiter='\t')
    out_csv = csv.writer(open(fnFront + '.csv', 'w+', newline=''))
    for row in tqdm(in_txt):
        out_csv.writerow(row)
