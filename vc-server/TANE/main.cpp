#include "TANE.hpp"
#include <boost/python.hpp>

using std::string;

BOOST_PYTHON_MODULE(tane)
{
  using namespace boost::python;
  def("runTANE", runTANE);
}

int runTANE(string fp)
{
    double start, stop, durationTime;
    TANE tane = TANE();
    start = clock();
    tane.run(fp);
    stop = clock();
    durationTime = ((double)(stop - start)) / CLOCKS_PER_SEC;
    cout << durationTime << "s" << endl;
    return 0;
}

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
