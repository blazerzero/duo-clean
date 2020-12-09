import subprocess as sp
import analyze
import contextlib

scenarios = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
methods = ['bayes', 'min']

for m in methods:
    for s in scenarios:
        # f_out = open('./analysis-results/analyze-out-' + str(s) + '-' + m, 'w')

        # cmd = 'python analyze.py ' + str(s) + ' ' + m
        # p = sp.Popen(cmd, stdout=f_out, stderr=f_err)
        # output = p.communicate()[0]
        with open('./analysis-results/analyze-out-' + str(s) + '-' + m + '.txt', 'w') as f:
            with contextlib.redirect_stdout(f):
                analyze.main(['analyze.py', str(s), m])

        # f_out.close()
        # f_err.close()
