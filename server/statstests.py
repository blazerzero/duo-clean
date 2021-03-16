# Loading the packages
import copy
import pandas as pd
import numpy as np
import scipy as sp
import statsmodels.tsa.stattools as sm
import pmdarima
import sys
import pymannkendall as mk
import helpers
import json
from rich.console import Console

console = Console()

def adf(data):

    # Applying ADF Test:
    result = sm.adfuller(data)

    # Printing the results (Table under Figure A):
    output = pd.Series(result[0:4], index=['t-statistic','p-value','lags-used','no-of-observations'])
    for key, value in result[4].items():
        output['Critical Value (%s)'%key] = value
    
    console.print(output)

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
    
    # console.print(output)

def pp(data):

    # Conducting PP test:
    test = pmdarima.arima.PPTest() # You can choose alpha here, default = 0.05
    result = test.should_diff(data)
    console.print(result)

def mannkendall(data):
    result = mk.original_test(data)
    console.print(result)

if __name__ == '__main__':
    data = None
    run_type = sys.argv[1]
    project_id = sys.argv[2]
    test = sys.argv[3]
    # metric = sys.argv[4]
    if len(sys.argv) < 5:
        metrics = [
            'st_vio_precision',
            'mt_vio_precision',
            'mt_2_vio_precision',
            'mt_3_vio_precision',
            'lt_vio_precision',
            'st_vio_recall',
            'mt_vio_recall',
            'mt_2_vio_recall',
            'mt_3_vio_recall',
            'lt_vio_recall',
            'st_vio_f1',
            'mt_vio_f1',
            'mt_2_vio_f1',
            'mt_3_vio_f1',
            'lt_vio_f1'
        ]
    else:
        metrics = sys.argv[4:]
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
    alt_fds = project_info['scenario']['alt_h']

    h_space = project_info['scenario']['hypothesis_space']
    clean_h_space = project_info['scenario']['clean_hypothesis_space']
    study_metrics, fd_metadata = helpers.deriveStats(
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

    console.print('\n*** Target Hypothesis ***\n')
    for metric in metrics:
        console.print(metric)
        data = pd.DataFrame(columns = ['iter_num', metric])
        if metric in study_metrics.keys():
            data['iter_num'] = [i['iter_num'] for i in study_metrics[metric]]
            data[metric] = [i['value'] for i in study_metrics[metric]]
            data = data.set_index('iter_num')[:-1]
            if test == 'adf':
                adf(data)
            elif test == 'pp':
                pp(data)
            elif test == 'mk':
                norm_data = list()
                formatted_data = data[metric].to_list()
                for i in range(0, len(formatted_data)):
                    if i == 0:
                        norm_data.append(formatted_data[i])
                    elif i == 1:
                        norm_data.append(np.mean([formatted_data[i], formatted_data[i-1]]))
                    else:
                        norm_data.append(np.mean([formatted_data[i], formatted_data[i-1], formatted_data[i-2]]))
                # console.print(norm_data)
                mannkendall(norm_data)
        elif metric in fd_metadata[project_info['scenario']['target_fd']].keys():
            for fd_m in fd_metadata.values():
                data['iter_num'] = [i['iter_num'] for i in fd_m[metric]]
                data[metric] = [i['iter_num'] for i in fd_m[metric]]
                data = data.set_index('iter_num')[:-1]
                if test == 'adf':
                    adf(data)
                elif test == 'pp':
                    pp(data)
                elif test == 'mannkendall':
                    norm_data = list()
                    formatted_data = data[metric].to_list()
                    for i in range(0, len(formatted_data)):
                        if i == 0:
                            norm_data.append(formatted_data[i])
                        elif i == 1:
                            norm_data.append(np.mean([formatted_data[i], formatted_data[i-1]]))
                        else:
                            norm_data.append(np.mean([formatted_data[i], formatted_data[i-1], formatted_data[i-2]]))
                    console.print(norm_data)
                    mannkendall(norm_data)
        console.print()

    for h in alt_fds:
        study_metrics, fd_metadata = helpers.deriveStats(
            interaction_metadata,
            fd_metadata,
            h_space,
            study_metrics,
            dirty_dataset,
            clean_dataset,
            h
        )
        console.print('\n*** Alternative Hypothesis:', h, '***\n')
        for metric in metrics:
            console.print(metric)
            data = pd.DataFrame(columns = ['iter_num', metric])
            if metric in study_metrics.keys():
                data['iter_num'] = [i['iter_num'] for i in study_metrics[metric]]
                data[metric] = [i['value'] for i in study_metrics[metric]]
                data = data.set_index('iter_num')[:-1]
                if test == 'adf':
                    adf(data)
                elif test == 'pp':
                    pp(data)
                elif test == 'mk':
                    norm_data = list()
                    formatted_data = data[metric].to_list()
                    for i in range(0, len(formatted_data)):
                        if i == 0:
                            norm_data.append(formatted_data[i])
                        elif i == 1:
                            norm_data.append(np.mean([formatted_data[i], formatted_data[i-1]]))
                        else:
                            norm_data.append(np.mean([formatted_data[i], formatted_data[i-1], formatted_data[i-2]]))
                    # console.print(norm_data)
                    mannkendall(norm_data)
            elif metric in fd_metadata[project_info['scenario']['target_fd']].keys():
                for fd_m in fd_metadata.values():
                    data['iter_num'] = [i['iter_num'] for i in fd_m[metric]]
                    data[metric] = [i['iter_num'] for i in fd_m[metric]]
                    data = data.set_index('iter_num')[:-1]
                    if test == 'adf':
                        adf(data)
                    elif test == 'pp':
                        pp(data)
                    elif test == 'mannkendall':
                        norm_data = list()
                        formatted_data = data[metric].to_list()
                        for i in range(0, len(formatted_data)):
                            if i == 0:
                                norm_data.append(formatted_data[i])
                            elif i == 1:
                                norm_data.append(np.mean([formatted_data[i], formatted_data[i-1]]))
                            else:
                                norm_data.append(np.mean([formatted_data[i], formatted_data[i-1], formatted_data[i-2]]))
                        console.print(norm_data)
                        mannkendall(norm_data)
            console.print()

