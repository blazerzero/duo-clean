#ifndef UTIL_OUTPUT_H_
#define UTIL_OUTPUT_H_

#include <iostream>
#include <ostream>
#include "../data/database.h"
#include "../algorithms/minernode.h"
#include "../data/cfd.h"

class Output {
public:
	template <typename T>
    static void printCollection(const T& coll, std::ostream& out=std::cout) {
		for (const typename T::value_type& i : coll) {
			out << i << " ";
		}
	}

    template<typename T>
    static void printCollection(const T& items, const std::string& join, std::ostream& out=std::cout) {
        bool comma = false;
        for (const typename T::value_type& item : items) {
            if (comma) {
                out << join;
            }
            else {
                comma = true;
            }
            out << item;
        }
    }

    static void printItemset(const Itemset& items, const Database& db, std::ostream& out=std::cout, bool endl=true) {
        out << "(";
        std::vector<std::string> parts;
        for (uint ix = 0; ix < items.size(); ix++) {
            int item = items[ix];
            if (item < 0) {
                std::string attr = db.getAttrName(-1-item);
                attr.erase(std::remove(attr.begin(), attr.end(), '\r'), attr.end());
                parts.push_back(attr);
            }
            else if (item == 0) {
                std::string attr = db.getAttrName(ix);
                attr.erase(std::remove(attr.begin(), attr.end(), '\r'), attr.end());
                parts.push_back(attr + "=N/A");
            }
            else {
                std::string attr = db.getAttrName(db.getAttrIndex(item));
                attr.erase(std::remove(attr.begin(), attr.end(), '\r'), attr.end());
                parts.push_back(attr + "=" + db.getValue(item));
            }
        }
        printCollection(parts, ", ", out);
        out << ")";
        if (endl) {
            out << std::endl;
        }
    }

    static void printCFDList(const CFDList& cs, const Database& db, std::ostream& out=std::cout, bool endl=true) {
        for (const auto& c : cs) {
            printCFD(c.first, c.second, db, out, endl);
        }
    }

    static void printCFD(const CFD& c, const Database& db, std::ostream& out=std::cout, bool endl=true) {
        printCFD(c.first, c.second, db, out, endl);
    }

    static void printCFD(const CFDPlus& c, const Database& db, std::ostream& out=std::cout, bool endl=true) {
        printCFDWithConfidence(c.first.first, c.first.second, c.second, db, out, endl);
    }

    static void printCFD(const Itemset& lhs, const int rhs, const Database& db, std::ostream& out=std::cout, bool endl=true) {
        printItemset(lhs, db, out, false);
        out << " => ";
        if (rhs < 0) {
            std::string rhsAttr = db.getAttrName(-1-rhs);
            rhsAttr.erase(remove(rhsAttr.begin(), rhsAttr.end(), '\r'), rhsAttr.end());
            out << rhsAttr;
        }
        else {
            std::string rhsAttr = db.getAttrName(db.getAttrIndex(rhs));
            rhsAttr.erase(remove(rhsAttr.begin(), rhsAttr.end(), '\r'), rhsAttr.end());
            out << (rhsAttr + "=" + db.getValue(rhs));
        }
        if (endl) {
            out << std::endl;
        }
    }

    static void printCFDWithConfidence(const Itemset& lhs, const int rhs, const double conf, const Database& db, std::ostream& out=std::cout, bool endl=true) {
        out << "{\"cfd\": \"";
        printItemset(lhs, db, out, false);
        out << " => ";
        if (rhs < 0) {
            std::string rhsAttr = db.getAttrName(-1-rhs);
            rhsAttr.erase(remove(rhsAttr.begin(), rhsAttr.end(), '\r'), rhsAttr.end());
            out << rhsAttr;
        }
        else {
            std::string rhsAttr = db.getAttrName(db.getAttrIndex(rhs));
            rhsAttr.erase(remove(rhsAttr.begin(), rhsAttr.end(), '\r'), rhsAttr.end());
            out << (rhsAttr + '=' + db.getValue(rhs));
        }
        out << "\", ";
        out << ("\"conf\": " + std::to_string(conf) + "},");
        if (endl) {
            out << std::endl;
        }
    }

    static bool sortByConfidence(const std::pair<CFD, double> &a, const std::pair<CFD, double> &b) {
        return (a.second > b.second);
    }
};

#endif //UTIL_OUTPUT_H_
