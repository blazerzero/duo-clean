import sys
import matplotlib.pyplot as plt
import numpy as np

if __name__ == '__main__':
    for s in range(0, 17):
        if sys.argv[1] == 'informed':
            fp_start = './results/informed-bayesian/informed-bayesian-sim-out-'
        elif sys.argv[1] == 'uninformed':
            fp_start = './results/uninformed-bayesian/uninformed-bayesian-sim-out-'
        else:
            fp_start = './results/oracle/oracle-sim-out'
        with open(fp_start + str(s) + '.txt', 'r') as f:
            output = f.read()
        keyword = 'Results:\n'
        _, _, after = output.partition(keyword)
        fd_lines = after.split('\n')

        fig, ax1 = plt.subplots()
        ax1.set_ylabel('p(h | X)')
        ax1.set_xlabel('Iteration #')
        ax1.set_title('Scenario #' + str(s) + ': Probability of Each Hypothesis Over the Interaction')
        ax1.set_xticks(np.arange(0, 30, 5.0))

        for line in fd_lines:
            if 'Done' in line or not line.strip():
                continue
            fd = line.split(': ')[0]
            p_history = [float(i) for i in line.split(': ')[1].split(', ')]
            print(fd + ': ' + repr(p_history))
            ax1.plot([i for i in range(1, 26)], p_history)

        fig.tight_layout()
        if sys.argv[1] == 'informed' or sys.argv[1] == 'uninformed':
            fig.savefig('../plots/sim-bayesian-' + sys.argv[1] + '-scenario-' + str(s) + '-p(h|X).jpg')
        else:
            fig.savefig('../plots/sim-' + sys.argv[1] + '-scenario-' + str(s) + '-p(h|X).jpg')
        plt.clf()
    print('[SUCCESS]')
