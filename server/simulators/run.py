import subprocess as sp

scenarios = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
simulators = ['oracle', 'informed-bayesian', 'uninformed-bayesian']

for sim in simulators:
    # f_out = open(sim + '-sim-out.txt', 'w')
    # f_out.seek(0,0)
    # f_out.truncate()
    # f_err = open(sim + '-sim-err.txt', 'w')
    # f_err.seek(0,0)
    # f_err.truncate()

    for s in scenarios:
        if sim == 'informed-bayesian':
            f_out = open('./results/informed-bayesian/' + sim + '-sim-out-' + str(s) + '.txt', 'w')
            f_err = open('./results/informed-bayesian/' + sim + '-sim-err-' + str(s) + '.txt', 'w')
            cmd = 'yarn run bayesian ' + str(s) + ' informed'
        elif sim == 'uninformed-bayesian':
            f_out = open('./results/uninformed-bayesian/' + sim + '-sim-out-' + str(s) + '.txt', 'w')
            f_err = open('./results/uninformed-bayesian/' + sim + '-sim-err-' + str(s) + '.txt', 'w')
            cmd = 'yarn run bayesian ' + str(s) + ' uninformed'
        else:
            f_out = open('./results/oracle/' + sim + '-sim-out' + str(s) + '.txt', 'w')
            f_err = open('./results/oracle/' + sim + '-sim-err' + str(s) + '.txt', 'w')
            cmd = 'yarn run ' + sim + ' ' + str(s)
        p = sp.Popen(cmd, stdout=f_out, stderr=f_err, shell=True)
        output = p.communicate()[0]
    
    f_out.close()
    f_err.close()