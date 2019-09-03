#pragma once

#include <iostream>
#include <fstream>
#include <string>
#include <unordered_map>
#include <map>
#include <set>
#include <vector>
#include <algorithm>
#include <time.h>
using namespace std;

typedef int Node;
typedef int Attribute;
typedef set<Node> Set;
enum Category {none, not_none, dependency, minimal_dependency, candidate_dependency, non_dependency, maximal_non_dependency, candidate_non_dependency};
class DFD;

class Pair
{
public:
	Pair(int a, int b) : a(a), b(b) {};
	~Pair() {};

	bool operator == (const Pair p) { return (a == p.a) && (b == p.b); };
	bool operator < (const Pair p) const { return (a < p.a) && (b < p.b); };
	int a;
	int b;
};

class AttrDFD 
{
public:

	AttrDFD(DFD * father): super(father) {}
	~AttrDFD() {}

	bool isVisited(Node n);
	bool isCandidate(Node n);
	bool isDependency(Node n);
	bool isNonDependency(Node n);
	bool isMinimal(Node n);  // check all subsets of the current node to see if it is a minimal dependency, in the case that it is a candidate. 
	bool isMaximal(Node n);  // check all supersets of the current node to see if it is a maximal dependency, in the case that it is a candidate. 
	void addDependency(Node n);
	void addNonDependency(Node n);
	void addDepCandidate(Node n);
	void addNonDepCandidate(Node n);
	void removeDepCandidate(Node n);
	void removeNonDepCandidate(Node n);
	void updateDependencyType(Node n, Category before);  // alter the dependency type of a particular node after a candidate changes to a dependency or a non-dependency
	Category getCategory(Node n);

	void inferCategory(Node n);  // examines if the	node is a proper superset / subset of a previously discovered dependency / non - dependency and updates its category accordingly
	int computePartitions(Node n, Node old_n, Attribute a);  // the same with tane.
	int getPartition(Node n, Node old_n);
	void addTrace(Node n);
	Node getTrace();

	Node pickNextNode(Node n);
	Set getPrunedSubsets(Node n);
	Set getPrunedSupersets(Node n);

	Set generateNextSeeds();
	Set minimizeSeeds(Set s);
	Set set_difference(Set a, Set b);

	Set dependencies;

	unordered_map<Node, bool> visited;
	unordered_map<Node, bool> dependency;
	unordered_map<Node, bool> non_dependency;
	unordered_map<Node, bool> minimal_dependency;
	unordered_map<Node, bool> maximal_non_dependency;
	unordered_map<Node, bool> candidate_dependency;
	unordered_map<Node, bool> candidate_non_dependency;

	vector<Node> attrs;

private:
	DFD * super;
	Set seeds;
	vector<Node> trace;
	Set non_dependencies;
};

class DFD
{
public:

	DFD() { attr_solver = new AttrDFD(this); }
	~DFD() {}

	void open(string file);

	void solve();
	Set findLHSs(Attribute attr);
	void output();
	bool compare(int a, int b);

public:
	int column_len;
	int row_len;
	vector<Node> attrs;
	vector<vector<int>> * partitions;
	int * partitions_len;
	bool * partitions_checked;
	Set unique_attrs;
	vector<vector<int>> data;
	AttrDFD * attr_solver;
	vector<vector<Node>> fd;
};

vector<string> split(string, char);
