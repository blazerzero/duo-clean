import subprocess as sp

scenarios = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]

for s in scenarios:
    cmd = 'yarn run oracle ' + str(s)
    f_std = open('./sim-out.txt', 'a')
    f_err = open('./sim-err.txt', 'a')
    p = sp.Popen(cmd, stdout=f_std, stderr=f_err, shell=True)
    output = p.communicate()[0]