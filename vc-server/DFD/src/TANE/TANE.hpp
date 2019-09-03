#ifndef TANE_hpp
#define TANE_hpp

#include <string>
#include <sstream>
#include <iostream>
#include <fstream>
#include <map>
#include <unordered_map>
#include <set>
#include <algorithm>
#include "FD.hpp"
#include "time.h"

class TANE
{
private:
    string inputFilePath;
    string outputFilePath;
    int rowNum;
    int columnNum;
    vector<vector<int>> db;
    vector<unordered_map<string,int>> dict;
    int R;
    vector<set<int>> level;
    int * CPlus;
    vector<vector<int>> * PI;
    vector<FD> FDResult;

    // for PI Product
    vector<int> T;
    vector<vector<int>> S;
    vector<int> empty;

public:
    TANE();
    void run(string inputPath);
    ~TANE(){}
    void readFile();
    void mineFD();
    void outputResult();

public:
    void computeDependencies(int l);
    void prune(int l);
    void generateNextLevel(int l);

    set<set<int>> getPrefixBlocks(int l);
    bool isValidFd(int s, int A);

    int getPI(int X);
    void calcPISingleton(int A);
    void calcPIProduct(int X, int A, int B);

    int getSingleAttr(int X);
    void addResult(int X, int A);

};

// utils
vector<string> split(string s, char delim);

#endif
