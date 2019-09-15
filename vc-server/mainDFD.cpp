#include "DFD.h"

int main(int argc, char** argv)
{
	DFD dfd;
	double a, b;
	a = clock();
	//cout << "run!" << endl;
	dfd.open(argv[1]);
	dfd.solve(argv[2]);
	b = clock();
	cout << (b - a) / CLOCKS_PER_SEC << 's' << endl;
	return 0;
}
