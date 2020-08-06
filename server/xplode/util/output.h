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
                attr.erase(std::remove(attr.begin(), attr.end(), '\t'), attr.end());
                attr.erase(std::remove(attr.begin(), attr.end(), '\n'), attr.end());
                char attrEnd = attr.back();
                if ((int)attrEnd < 65 || (int)attrEnd > 122) {
                    attr.pop_back();
                }
                char attrFront = attr.front();
                if ((int)attrFront < 65 || (int)attrFront > 122) {
                    attr = attr.substr(3);
                }
                // trim(attr);
                parts.push_back(attr);
            }
            else if (item == 0) {
                std::string attr = db.getAttrName(ix);
                attr.erase(std::remove(attr.begin(), attr.end(), '\r'), attr.end());
                attr.erase(std::remove(attr.begin(), attr.end(), '\t'), attr.end());
                attr.erase(std::remove(attr.begin(), attr.end(), '\n'), attr.end());
                char attrEnd = attr.back();
                if ((int)attrEnd < 65 || (int)attrEnd > 122) {
                    attr.pop_back();
                }
                char attrFront = attr.front();
                if ((int)attrFront < 65 || (int)attrFront > 122) {
                    attr = attr.substr(3);
                }
                // trim(attr);
                parts.push_back(attr + "=N/A");
            }
            else {
                std::string attr = db.getAttrName(db.getAttrIndex(item));
                attr.erase(remove(attr.begin(), attr.end(), '\r'), attr.end());
                attr.erase(remove(attr.begin(), attr.end(), '\t'), attr.end());
                attr.erase(remove(attr.begin(), attr.end(), '\n'), attr.end());
                char attrEnd = attr.back();
                if ((int)attrEnd < 65 || (int)attrEnd > 122) {
                    attr.pop_back();
                }
                char attrFront = attr.front();
                if ((int)attrFront < 65 || (int)attrFront > 122) {
                    attr = attr.substr(3);
                }
                std::string value = db.getValue(item);
                value.erase(remove(value.begin(), value.end(), '\r'), value.end());
                value.erase(remove(value.begin(), value.end(), '\t'), value.end());
                value.erase(remove(value.begin(), value.end(), '\n'), value.end());
                if ((int)value.back() < 65 || (int)value.back() > 122) {
                    value.pop_back();
                }
                if ((int)value.front() < 65 || (int)value.front() > 122) {
                    value = value.substr(3);
                }
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
            std::cout << "\t\t";
            printCFDWithConfidence(c.first.first, c.first.second, c.second, db, out, endl);
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
            rhsAttr.erase(remove(rhsAttr.begin(), rhsAttr.end(), '\t'), rhsAttr.end());
            rhsAttr.erase(remove(rhsAttr.begin(), rhsAttr.end(), '\n'), rhsAttr.end());
            char attrEnd = rhsAttr.back();
            if ((int)attrEnd < 65 || (int)attrEnd > 122) {
                rhsAttr.pop_back();
            }
            char attrFront = rhsAttr.front();
            if ((int)attrFront < 65 || (int)attrFront > 122) {
                rhsAttr = rhsAttr.substr(3);
            }
            // trim(rhsAttr);
            out << rhsAttr;
        }
        else {
            std::string rhsAttr = db.getAttrName(db.getAttrIndex(rhs));
            rhsAttr.erase(remove(rhsAttr.begin(), rhsAttr.end(), '\r'), rhsAttr.end());
            rhsAttr.erase(remove(rhsAttr.begin(), rhsAttr.end(), '\t'), rhsAttr.end());
            rhsAttr.erase(remove(rhsAttr.begin(), rhsAttr.end(), '\n'), rhsAttr.end());
            char attrEnd = rhsAttr.back();
            if ((int)attrEnd < 65 || (int)attrEnd > 122) {
                rhsAttr.pop_back();
            }
            char attrFront = rhsAttr.front();
            if ((int)attrFront < 65 || (int)attrFront > 122) {
                rhsAttr = rhsAttr.substr(3);
            }
            std::string rhsValue = db.getValue(rhs);
            rhsValue.erase(remove(rhsValue.begin(), rhsValue.end(), '\r'), rhsValue.end());
            rhsValue.erase(remove(rhsValue.begin(), rhsValue.end(), '\t'), rhsValue.end());
            rhsValue.erase(remove(rhsValue.begin(), rhsValue.end(), '\n'), rhsValue.end());
            if ((int)rhsValue.back() < 65 || (int)rhsValue.back() > 122) {
                rhsValue.pop_back();
            }
            if ((int)rhsValue.front() < 65 || (int)rhsValue.front() > 122) {
                rhsValue = rhsValue.substr(3);
            }
            // trim(rhsAttr);
            // trim(rhsValue);
            out << (rhsAttr + '=' + rhsValue);
        }
        out << "\", ";
        out << ("\"score\": " + std::to_string(conf) + "},");
        if (endl) {
            out << std::endl;
        }
    }

    static bool sortByConfidence(const std::pair<CFD, double> &a, const std::pair<CFD, double> &b) {
        return (a.second > b.second);
    }

    static std::string& ltrim(std::string& str, const std::string& chars = " ") {
        str.erase(0, str.find_first_not_of(chars));
        return str;
    }
    
    static std::string& rtrim(std::string& str, const std::string& chars = " ") {
        str.erase(str.find_last_not_of(chars) + 1);
        return str;
    }
    
    static std::string& trim(std::string& str, const std::string& chars = " ") {
        return ltrim(rtrim(str, chars), chars);
    }
};

#endif //UTIL_OUTPUT_H_
