#include "DFD.h"

int main() 
{
	DFD dfd;
	double a, b;
	a = clock();
	dfd.open("input file path");
	dfd.solve();
	b = clock();
	cout << (b - a) / CLOCKS_PER_SEC << 's' << endl;
	return 0;
}
