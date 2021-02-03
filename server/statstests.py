# Loading the packages
import pandas as pd
import numpy as np
import scipy as sp
import statsmodels.tsa.stattools as sm
import pmdarima
import sys
import pymannkendall as mk
import plot_results
import json

def adf(data):

    # Applying ADF Test:
    result = sm.adfuller(data)

    # Printing the results (Table under Figure A):
    output = pd.Series(result[0:4], index=['t-statistic','p-value','lags-used','no-of-observations'])
    for key, value in result[4].items():
        output['Critical Value (%s)'%key] = value
    
    print(output)

    # Apply transformation to make data stationary:
    # log_data = np.log(data) # Taking the log
    # ma_data = log_data.rolling(window=12).mean() # Taking moving average
    # log_minus_ma_data = log_data - ma_data
    # log_minus_ma_data.dropna(inplace=True)

    # Applying ADF Test after applying transformations:
    # st_test = sm.adfuller(log_minus_ma_data)

    # Printing the results (Table under Figure B):
    # output = pd.Series(st_test[0:4], index=['t-statistic','p-value','lags-used','no-of-observations'])
    # for key,value in st_test[4].items():
    #     output['Critical Value (%s)'%key] = value
    
    # print(output)

def pp(data):

    # Conducting PP test:
    test = pmdarima.arima.PPTest() # You can choose alpha here, default = 0.05
    result = test.should_diff(data)
    print(result)

def mannkendall(data):
    result = mk.original_test(data)
    print(result)

if __name__ == '__main__':
    data = None
    run_type = sys.argv[1]
    project_id = sys.argv[2]
    test = sys.argv[3]
    metric = sys.argv[4]
    pathstart = './docker-out/' if run_type == 'real' else './store/'

    with open(pathstart + project_id + '/study_metrics.json', 'r') as f:
        study_metrics = json.load(f)
    with open(pathstart + project_id + '/fd_metadata.json', 'r') as f:
        fd_metadata = json.load(f)
    with open(pathstart + project_id + '/project_info.json', 'r') as f:
        project_info = json.load(f)
    with open(pathstart + project_id + '/interaction_metadata.json', 'r') as f:
        interaction_metadata = json.load(f)
    dirty_dataset = pd.read_csv(project_info['scenario']['dirty_dataset'], keep_default_na=False)
    clean_dataset = pd.read_csv(project_info['scenario']['clean_dataset'], keep_default_na=False)
    target_fd = project_info['scenario']['target_fd']

    h_space = project_info['scenario']['hypothesis_space']
    clean_h_space = project_info['scenario']['clean_hypothesis_space']
    if 'lt_vio_precision' not in study_metrics.keys():
        study_metrics, fd_metadata = plot_results.deriveStats(
            interaction_metadata,
            fd_metadata,
            h_space,
            study_metrics,
            dirty_dataset,
            clean_dataset,
            target_fd
        )
        
        with open(pathstart + project_id + '/study_metrics.json', 'w') as f:
            json.dump(study_metrics, f, indent=4)
        with open(pathstart + project_id + '/fd_metadata.json', 'w') as f:
            json.dump(fd_metadata, f, indent=4)

    data = pd.DataFrame(columns = ['iter_num', metric])
    if metric in study_metrics.keys():
        data['iter_num'] = [i['iter_num'] for i in study_metrics[metric]]
        data[metric] = [i['value'] for i in study_metrics[metric]]
        data = data.set_index('iter_num')
        if test == 'adf':
            adf(data)
        elif test == 'pp':
            pp(data)
        elif test == 'mk':
            mannkendall(data[metric].to_list())
    elif metric in fd_metadata[project_info['scenario']['target_fd']].keys():
        for fd_m in fd_metadata.values():
            data['iter_num'] = [i['iter_num'] for i in fd_m[metric]]
            data[metric] = [i['iter_num'] for i in fd_m[metric]]
            data = data.set_index('iter_num')
            if test == 'adf':
                adf(data)
            elif test == 'pp':
                pp(data)
            elif test == 'mannkendall':
                mannkendall(data[metric].to_list())

    
