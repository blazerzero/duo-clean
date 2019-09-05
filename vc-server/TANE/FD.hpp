#ifndef FD_hpp
#define FD_hpp
#include<vector>
#include<set>
using namespace std;

struct FD
{
    vector<int> left;
    int right;
};

bool FDResultCmp(const FD &first, const FD &second);

#endif
