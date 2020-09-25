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
                trim(attr);
                parts.push_back(attr);
            }
            else if (item == 0) {
                std::string attr = db.getAttrName(ix);
                trim(attr);
                parts.push_back(attr + "=N/A");
            }
            else {
                std::string attr = db.getAttrName(db.getAttrIndex(item));
                std::string value = db.getValue(item);
                trim(attr);
                trim(value);
                parts.push_back(attr + "=" + value);
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

    static void printCFDList(const CFDPlusList& cs, const Database& db, std::ostream& out=std::cout, bool endl=true) {
        for (const auto& c : cs) {
            printCFDWithConfidence(c.first.first, c.first.second, c.second.first, c.second.second, db, out, endl);
        }
    }

    static void printCFD(const CFD& c, const Database& db, std::ostream& out=std::cout, bool endl=true) {
        printCFD(c.first, c.second, db, out, endl);
    }

    static void printCFD(const CFDPlus& c, const Database& db, std::ostream& out=std::cout, bool endl=true) {
        printCFDWithConfidence(c.first.first, c.first.second, c.second.first, c.second.second, db, out, endl);
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
        /* if (endl) {
            out << std::endl;
        } */
    }

    static void printCFDWithConfidence(const Itemset& lhs, const int rhs, const double conf, const double support, const Database& db, std::ostream& out=std::cout, bool endl=true) {
        out << "{\"cfd\": \"";
        printItemset(lhs, db, out, false);
        out << " => ";
        if (rhs < 0) {
            std::string rhsAttr = db.getAttrName(-1-rhs);
            trim(rhsAttr);
            out << rhsAttr;
        }
        else {
            std::string rhsAttr = db.getAttrName(db.getAttrIndex(rhs));
            std::string rhsValue = db.getValue(rhs);
            trim(rhsAttr);
            trim(rhsValue);
            out << (rhsAttr + '=' + rhsValue);
        }
        out << "\", ";
        out << ("\"score\": " + std::to_string(conf) + ", \"support\": " + std::to_string(support) + "},");
        /* if (endl) {
            out << std::endl;
        } */
    }

    static bool sortByConfidence(const std::pair<CFD, Metrics> &a, const std::pair<CFD, Metrics> &b) {
        return (a.second.first > b.second.first);
    }

    static std::string& ltrim(std::string& str, const std::string& chars = "\t\n\v\f\r\xef\xbb\xbf ") {
        str.erase(0, str.find_first_not_of(chars));
        return str;
    }
    
    static std::string& rtrim(std::string& str, const std::string& chars = "\t\n\v\f\r\xef\xbb\xbf ") {
        str.erase(str.find_last_not_of(chars) + 1);
        return str;
    }
    
    static std::string& trim(std::string& str, const std::string& chars = "\t\n\v\f\r\xef\xbb\xbf ") {
        return ltrim(rtrim(str, chars), chars);
    }
};

#endif //UTIL_OUTPUT_H_
