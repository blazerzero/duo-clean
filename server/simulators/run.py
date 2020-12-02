import subprocess as sp
import os

scenarios = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
simulators = ['oracle', 'anti-oracle', 'learner']

for sim in simulators:
    f_std = open(sim + '-sim-out.txt', 'a')
    f_std.seek(0,0)
    f_std.truncate()
    f_err = open(sim + '-sim-err.txt', 'a')
    f_err.seek(0,0)
    f_err.truncate()
    
    for s in scenarios:
        cmd = 'yarn run ' + sim + ' ' + str(s)
        p = sp.Popen(cmd, stdout=f_std, stderr=f_err, shell=True)
        output = p.communicate()[0]