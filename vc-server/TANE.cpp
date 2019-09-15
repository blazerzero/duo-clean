#include "TANE.hpp"

TANE::TANE()
{
    R = 0;
    rowNum = 0;
    columnNum = 0;
    /*inputFilePath = "data.txt";
    outputFilePath = "result.txt";
    T.resize(100000,-1);
    double start, stop, durationTime;
    start = clock();
    readFile();
    stop = clock();
    durationTime = ((double)(stop - start)) / CLOCKS_PER_SEC;
    cout << "Reading file Time: " << durationTime << "s" << endl;
    mineFD();
    outputResult();*/
}

void TANE::run(string inputPath, string outputPath)
{
    /*R = 0;
    rowNum = 0;
    columnNum = 0;*/
    inputFilePath = inputPath;
    outputFilePath = outputPath;
    //cout << inputFilePath << endl;
    T.resize(100000,-1);
    //double start, stop, durationTime;
   // start = clock();
    readFile();
    //stop = clock();
    //durationTime = ((double)(stop - start)) / CLOCKS_PER_SEC;
    //cout << "Reading file Time: " << durationTime << "s" << endl;
    cout << "done0" << endl;
    mineFD();
    cout << "done1" << endl;
    outputResult();
    cout << "done2" << endl;
}

void TANE::readFile()
{
    ifstream inFile;
    inFile.open(inputFilePath);
    string temp;
    // get columnNum first
    cout << inputFilePath << endl;
    if(!getline(inFile, temp))
    {
        cout << "Empty input file!" << endl;
        return;
    }
    // remove comma before whitespace
    for(int i = 0; i < temp.size() - 1; i++)
    {
        if(temp[i] == ',' && temp[i + 1] == ' ')
            temp[i] = '.';
    }
    vector<string> tempField = split(temp, ',');
    columnNum = tempField.size();
    for(int i = 0; i < columnNum; i++)
    {
        unordered_map<string,int> tempMap;
        dict.push_back(tempMap);
    }
    vector<int> tempInt;
    for(int i = 0; i < columnNum; i++)
    {
        if(dict[i].find(tempField[i]) != dict[i].end())
        {
            tempInt.push_back(dict[i][tempField[i]]);
        }
        else
        {
            int t = dict[i].size();
            tempInt.push_back(t);
            dict[i].insert(pair<string,int>(tempField[i],t));
        }
    }
    db.push_back(tempInt);
    rowNum++;

    cout << "dict done" << endl;

    for(int i = 0; i < columnNum; i++)
    {
        R += 1 << i;
    }
    CPlus = new int[R + 1];
    PI = new vector<vector<int>>[R + 1];
    while(getline(inFile, temp))
    {
        //remove comma before whitespace
        for(int i = 0; i < temp.size() - 1; i++)
        {
            if(temp[i] == ',' && temp[i + 1] == ' ')
            {
                temp[i] = '.';
            }
        }
        tempField = split(temp,',');
        vector<int> tempInt;
        for(int i = 0; i < columnNum; i++)
        {
            if(dict[i].find(tempField[i]) != dict[i].end())
            {
                tempInt.push_back(dict[i][tempField[i]]);
            }
            else
            {
                int t = dict[i].size();
                tempInt.push_back(t);
                dict[i].insert(pair<string,int>(tempField[i],t));
            }
        }
        db.push_back(tempInt);
        rowNum++;
    }
    inFile.close();
    cout << "done reading file" << endl;
}

void TANE::mineFD()
{
    set<int> level_0;
    level.push_back(level_0);
    int empty = 0;
    CPlus[0] = R;
    set<int> level_1;
    for(int i = 0; i < columnNum; i++)
    {
        int t = 1 << i;
        level_1.insert(t);
        calcPISingleton(t);
    }
    level.push_back(level_1);
    int l = 1;
    while(!level[l].empty())
    {
        computeDependencies(l);
        prune(l);
        generateNextLevel(l);
        l = l + 1;
    }
}

void TANE::computeDependencies(int l)
{
    // for each X in Ll do..
    for(auto iter_i : level[l])
    {
        int X = iter_i;
        CPlus[X] = R;
        for(int i = 0; i < columnNum; i++)
        {
            int t = 1 << i;
            if((t & X) == t)
            {
                CPlus[X] &= CPlus[X - t];
            }
        }
    }

    for(auto iter_i : level[l])
    {
        int X = iter_i;
        for(int i = 0; i < columnNum; i++)
        {
            int t = 1 << i;
            if((t & X & CPlus[X]) == t)
            {
                if(isValidFd(X - t, t))
                {
                    addResult(X - t, t);
                    CPlus[X] -= t;
                    CPlus[X] -= (CPlus[X] & (R - X));
                }
            }
        }
    }
}

void TANE::prune(int l)
{
	auto iter_i = level[l].begin();
    while(iter_i != level[l].end())
    {
        if(CPlus[*iter_i] == 0)
        {
            iter_i = level[l].erase(iter_i);
        }
		else
		{
			iter_i++;
		}
    }
}

void TANE::generateNextLevel(int l)
{
    set<int> level_lPlusOne;
    set<set<int>> prefix_blocks = getPrefixBlocks(l);
    for(auto iter_i : prefix_blocks)
    {
        set<int> K = iter_i;
        if(K.size() < 2) continue;
        for(auto iter_j = K.begin(); next(iter_j) != K.end(); iter_j++)
        {
            int Y = *iter_j;
            for(auto iter_k = next(iter_j); iter_k != K.end(); iter_k++)
            {
                int Z = *iter_k;
                int X = (Y | Z);
                bool addTo = true;
                for(int i = 0; i < columnNum; i++)
                {
                    int t = 1 << i;
                    if(X & t)
                    {
                        if(level[l].find(X - (X & t)) == level[l].end())
                        {
                            addTo = false;
                            break;
                        }
                    }
                }
                if(addTo == true)
                {
                    level_lPlusOne.insert(X);
                    calcPIProduct(X, Y, Z);
                }
            }
        }
    }
    //return L(l + 1)
    level.push_back(level_lPlusOne);
}

// output in order
void TANE::outputResult()
{
    ofstream outFile;
    outFile.open(outputFilePath, ios::out);
    if(!outFile)
    {
        cout << "Can't open output file!" << endl;
        return;
    }
    sort(FDResult.begin(), FDResult.end(), FDResultCmp);

    for(int i = 0; i < FDResult.size(); i++)
    {
        for(auto iter = FDResult[i].left.begin(); iter != FDResult[i].left.end(); iter++)
        {
            outFile << *iter << " ";
        }
        outFile << "-> ";
        outFile << FDResult[i].right << endl;
    }
    outFile.close();
}

bool TANE::isValidFd(int s, int A)
{
    // test if |PI(s)| == |PI(s union A)|
    if(s == 0) return false;
    int s_Plus_A = s | A;
    return getPI(s) == getPI(s_Plus_A);
}

int TANE::getPI(int X)
{
    return PI[X].size();
}

void TANE::calcPISingleton(int X)
{
    vector<vector<int>> t;
    int n;
    n = getSingleAttr(X);
    int temp;
    int tempIndex = 0;
    vector<vector<int>> tempSuperSet;
    unordered_map<int, int> tempMap;
    unordered_map<int, int>::iterator tempIt;
    for(int i = 0; i < db.size(); i++)
    {
        temp = db[i][n - 1];
        tempIt = tempMap.find(temp);
        if(tempIt == tempMap.end())
        {
            tempMap.insert(pair<int, int>(temp,tempIndex));
            tempIndex++;
            vector<int> tempSet;
            tempSet.push_back(i);
            tempSuperSet.push_back(tempSet);
        }
        else
            tempSuperSet[tempIt -> second].push_back(i);
    }
    for(auto a: tempSuperSet)
    {
        if(a.size() != 1)
            t.push_back(a);
    }
    PI[X] = t;
}

void TANE::calcPIProduct(int X, int A, int B)
{
    S.push_back(empty);
    vector<vector<int>> PITarget;
    int counter = 1;
    for(auto iter_i = PI[A].begin(); iter_i != PI[A].end(); iter_i++)
    {
        for(auto iter_j = (*iter_i).begin(); iter_j != (*iter_i).end(); iter_j++)
            T[*iter_j] = counter;
        S.push_back(empty);
        counter++;
    }
    for(auto iter_i = PI[B].begin(); iter_i != PI[B].end(); iter_i++)
    {
        for(auto iter_j = (*iter_i).begin(); iter_j != (*iter_i).end(); iter_j++)
        {
            if(T[*iter_j] != -1)
                S[T[*iter_j]].push_back(*iter_j);
        }
        for(auto iter_j = (*iter_i).begin(); iter_j != (*iter_i).end(); iter_j++)
        {
            if(T[*iter_j] != -1)
            {
                if(S[T[*iter_j]].size() >= 2)
                    PITarget.push_back(S[T[*iter_j]]);
                S[T[*iter_j]].clear();
            }
        }
    }
    PI[X] = PITarget;
    for(auto iter_i = PI[A].begin(); iter_i != PI[A].end(); iter_i++)
    {
        for(auto iter_j = (*iter_i).begin(); iter_j != (*iter_i).end(); iter_j++)
            T[*iter_j] = -1;
    }
    S.clear();
}

set<set<int>> TANE::getPrefixBlocks(int l)
{
    set<set<int>> re;
    map<int, set<int>> result;
    set<int> temp;
    set<int> empty;
    for(auto iter_i : level[l])
    {
        for(int i = columnNum - 1; i >= 0; i--)
        {
            int t = 1 << i;
            int prefix = iter_i - (iter_i & t);
            if(prefix != iter_i)
            {
                if(result.find(prefix) == result.end())
                    result[prefix] = empty;
                result[prefix].insert(iter_i);
                break;
            }
        }
    }
    for (auto it : result)
    {
        re.insert(it.second);
    }
    return re;
}

// get NO. of attibute, start from 1
int TANE::getSingleAttr(int X)
{
    for(int i = 0; i < columnNum; i++)
    {
        if((X >> i) & 1)
           return i + 1;
    }
    return -1;
}

// add an FD X -> A to FDResult
void TANE::addResult(int X, int A)
{
    FD fd;
    vector<int> v;
    for(int i = 0; i < columnNum; i++)
    {
        if((X >> i) & 1)
        {
            v.push_back(i + 1);
        }
    }
    fd.left = v;
    fd.right = getSingleAttr(A);
    FDResult.push_back(fd);

}

vector<string> split(string s, char delim)
{
    vector<string> result;
    stringstream ss(s);
    string temp;
    while(getline(ss,temp,delim))
        result.push_back(temp);
    return result;
}
