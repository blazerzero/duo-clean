import pandas as pd
import numpy as np
import random
import math
import sys

filename = sys.argv[1]
df = pd.read_csv(filename, encoding='latin_1')

sample_df = df.sample(n=int(sys.argv[2]), random_state=1)
sample_df.to_csv('out.csv', index=False)