#include "TANE.hpp"

using std::string;

int main(int argc, const char** argv)
{
    double start, stop, durationTime;
    string inputFP, outputFP;
    inputFP.assign(argv[1]);
    outputFP.assign(argv[2]);
    TANE tane = TANE();
    start = clock();
    tane.run(inputFP, outputFP);
    stop = clock();
    durationTime = ((double)(stop - start)) / CLOCKS_PER_SEC;
    cout << durationTime << "s" << endl;
    return 0;
}
