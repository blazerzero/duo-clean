import csv
import sys
import math
import pandas as pd
from tqdm import tqdm

def txt2csv(fn):
    #fnPieces = fn.split("/")
    fnFront = fn.split(".")[0]

    in_txt = csv.reader(open(fn, 'r'), delimiter='\t')
    out_csv = csv.writer(open(fnFront + '.csv', 'w+', newline=''))
    for row in tqdm(in_txt):
        out_csv.writerow(row)

'''
def streamlineGEDData(fn):
    df = pd.read_csv(fn, header=0, encoding = "ISO-8859-1", keep_default_na=False)
    count = 0
    for i in df.index:
        fullTitle = df.at[i, 'Full Title'].lower()
        print(fullTitle)
        if isinstance(fullTitle, str) == False:
            pass
        if 'administrator' in fullTitle:
            df.at[i, 'Title'] = 'Administrator'
        elif 'assistant' in fullTitle:
            df.at[i, 'Title'] = 'Assistant'
        elif 'director' in fullTitle:
            df.at[i, 'Title'] = 'Director'
        elif 'officer' in fullTitle:
            df.at[i, 'Title'] = 'Offier'
        elif 'advisor' in fullTitle:
            df.at[i, 'Title'] = 'Advisor'
        elif 'registrar' in fullTitle:
            df.at[i, 'Title'] = 'Registrar'
        elif 'coordinator' in fullTitle:
            df.at[i, 'Title'] = 'Coordinator'
        elif 'counsel' in fullTitle:
            df.at[i, 'Title'] = 'Counsel'
        elif 'analyst' in fullTitle:
            df.at[i, 'Title'] = 'Analyst'
        elif 'clerk' in fullTitle:
            df.at[i, 'Title'] = 'Clerk'
        elif 'manager' in fullTitle:
            df.at[i, 'Title'] = 'Manager'
        elif 'navigator' in fullTitle:
            df.at[i, 'Title'] = 'Navigator'
        elif 'coordinator' in fullTitle:
            df.at[i, 'Title'] = 'Coordinator'
        elif 'intern' in fullTitle:
            df.at[i, 'Title'] = 'Intern'
        elif 'student' in fullTitle:
            df.at[i, 'Title'] = 'Student'
        elif 'specialist' in fullTitle:
            df.at[i, 'Title'] = 'Specialist'
        elif 'biologist' in fullTitle:
            df.at[i, 'Title'] = 'Biologist'
        elif 'chemist' in fullTitle:
            df.at[i, 'Title'] = 'Chemist'
        elif 'physicist' in fullTitle:
            df.at[i, 'Title'] = 'Physician'
        elif 'doctor' in fullTitle:
            df.at[i, 'Title'] = 'Doctor'
        elif 'scientist' in fullTitle:
            df.at[i, 'Title'] = 'Scientist'
        elif 'physician' in fullTitle:
            df.at[i, 'Title'] = 'Physician'
        elif 'labourer' in fullTitle:
            df.at[i, 'Title'] = 'Labourer'
        elif 'mechanic' in fullTitle:
            df.at[i, 'Title'] = 'Mechanic'
        elif 'technician' in fullTitle:
            df.at[i, 'Title'] = 'Technician'
        elif 'supervisor' in fullTitle:
            df.at[i, 'Title'] = 'Supervisor'
        elif 'team lead' in fullTitle:
            df.at[i, 'Title'] = 'Team Lead'
        elif 'economist' in fullTitle:
            df.at[i, 'Title'] = 'Economist'
        elif 'trainee' in fullTitle:
            df.at[i, 'Title'] = 'Trainee'
        elif 'farm' in fullTitle:
            df.at[i, 'Title'] = 'Farm Worker'
        elif 'contractor' in fullTitle:
            df.at[i, 'Title'] = 'Contractor'
        elif 'engineer' in fullTitle:
            df.at[i, 'Title'] = 'Engineer'
        elif 'secretary' in fullTitle:
            df.at[i, 'Title'] = 'Secretary'
        elif 'consultant' in fullTitle:
            df.at[i, 'Title'] = 'Consultant'
        elif len(fullTitle) == 0:
            pass
        else:
            count -= 1
        count += 1
    print(count)
'''
