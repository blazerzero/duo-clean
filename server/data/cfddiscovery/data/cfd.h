#ifndef DATA_CFD_H_
#define DATA_CFD_H_

#include "types.h"

typedef std::pair<Itemset, int> CFD;
typedef std::pair<CFD, double> CFDPlus;
typedef std::vector<CFD> CFDList;
typedef std::vector<CFDPlus> CFDPlusList;
bool isValid(const Itemset& lhs, int rhs);

#endif //DATA_CFD_H_