#include "FD.hpp"

bool FDResultCmp(const FD &first, const FD &second)
{
    if(first.left != second.left)
    {
        auto iter_i = first.left.begin();
        auto iter_j = second.left.begin();
        
        while(iter_i != first.left.end() && iter_j != second.left.end())
        {
            if(*iter_i > *iter_j) return false;
            if(*iter_i < *iter_j) return true;
            iter_i++;
            iter_j++;
        }
        if(iter_i == first.left.end()) return true;
        if(iter_j == second.left.end()) return false;
    }
    else
        return first.right < second.right;
    return false;
}
