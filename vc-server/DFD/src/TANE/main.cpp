#include "TANE.hpp"

using std::string;

int main(int argc, const char** argv)
{
    double start, stop, durationTime;
    string fp;
    fp.assign(argv[1]);
    TANE tane = TANE();
    start = clock();
    tane.run(fp);
    stop = clock();
    durationTime = ((double)(stop - start)) / CLOCKS_PER_SEC;
    cout << durationTime << "s" << endl;
    return 0;
}
