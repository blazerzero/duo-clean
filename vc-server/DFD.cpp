#include "DFD.h"

Node AttrDFD::pickNextNode(Node n) {
	if (isDependency(n) && isCandidate(n))
	{
		Set s = getPrunedSubsets(n);
		if (s.empty())
			addDependency(n);
		else
		{
			Node next_node = *(s.begin());
			addTrace(n);
			return next_node;
		}
	}
	else if (isCandidate(n) && isNonDependency(n))
	{
		Set s = getPrunedSupersets(n);
		if (s.empty())
			addNonDependency(n);
		else
		{
			Node next_node = *(s.begin());
			addTrace(n);
			return next_node;
		}
	}
	if (!trace.empty())
	{
		return getTrace();
	}
	return 0;
}

Set AttrDFD::getPrunedSubsets(Node n) // 无需设置 visited and dependency and candidate
{
	Set result;
	for (auto it = attrs.begin(); it != attrs.end(); ++it)
	{
		if (*it == n) continue;
		Node subset = (*it) ^ n;
		if (subset > n)
			continue;
		if (!isVisited(subset))
		{
			result.insert(subset);
		}
	}
	return result;
}

Set AttrDFD::getPrunedSupersets(Node n) // 无需设置 visited and dependency and candidate
{
	Set result;
	for (auto it = attrs.begin(); it != attrs.end(); ++it)
	{
		if (*it == n) continue;
		Node superset = (*it) ^ n;
		if (superset < n)
			continue;
		if (!isVisited(superset))
		{
			result.insert(superset);
		}
	}
	return result;
}

Set AttrDFD::generateNextSeeds()
{
	Set seeds, new_seeds, result;
	if (!non_dependencies.empty())
	{
		for (auto max_non_dep = non_dependencies.begin();
			max_non_dep != non_dependencies.end();
			++max_non_dep)
		{
			Node compensate = ~(*max_non_dep);
			if (seeds.empty())
			{
				for (auto it = attrs.begin(); it != attrs.end(); ++it)
				{
					if ((*it) & compensate)
						seeds.insert(*it);
				}
			}
			else
			{
				for (auto dep : seeds)
				{
					for (auto it : attrs)
					{
						if (it & compensate)
							new_seeds.insert(dep + it - (it & dep));
					}
				}
				Set minimized_new_dep = minimizeSeeds(new_seeds);
				seeds.clear();
				for (auto new_seed : minimized_new_dep)
				{
					seeds.insert(new_seed);
				}
				new_seeds.clear();
			}
		}
		seeds = set_difference(seeds, dependencies);
		for (auto it : seeds)
		{
			if (isVisited(it)) continue;
			else result.insert(it);
		}
	}
	return result;
}

Set AttrDFD::minimizeSeeds(Set s) //如果有包含关系的只取子集
{
	Set result;
	bool * t = new bool[s.size()];
	for (int i = 0; i < s.size(); ++i) t[i] = true;
	int i(0), j(0);
	for (auto it : s)
	{
		if (!t[i]) continue;
		j = 0;
		for (auto it2 : s)
		{
			if (!t[j] || it == it2) continue;
			if (it != it2 && (it & it2) == it)
			{
				t[j] = false;
			}
			else if (it != it2 && (it & it2) == it2)
			{
				t[i] = false;
				break;
			}
			++j;
		}
		++i;
	}
	i = 0;
	for (auto it : s)
	{
		if (t[i])
		{
			result.insert(it);
		}
		++i;
	}
	return result;
}

Set AttrDFD::set_difference(Set a, Set b)
{
	Set c;
	if (!a.empty())
	{
		for (auto it : a)
		{
			if (b.find(it) == b.end())
			{
				c.insert(it);
			}
		}
	}
	return c;
}

Category AttrDFD::getCategory(Node n)
{
	if (!dependency[n] && !non_dependency[n])
	{
		return Category::none;
	}
	return Category::not_none;
}

void DFD::open(string inputFP) {
	ifstream inFile;
	inFile.open(inputFP);
	string temp;
	bool * duplicate = NULL;
	vector<unordered_map<string, int>> dict;
	if (!getline(inFile, temp))
	{
		cout << "Empty input file!" << endl;
		return;
	}
	// remove comma before whitespace
	for (int i = 0; i < temp.size() - 1; i++)
	{
		if (temp[i] == ',' && temp[i + 1] == ' ')
		{
			temp[i] = '.';
		}
	}
	Attribute a = 1;
	vector<string> tempField = split(temp, ',');
	column_len = tempField.size();
	duplicate = new bool[column_len];
	partitions = new vector<vector<int>> [(1 << column_len)];
	partitions_len = new int[(1 << column_len)];
	partitions_checked = new bool[(1 << column_len)];
	for (int i = 0; i < 1 << column_len ;++i)
	{
		partitions_len[i] = 0;
		partitions_checked[i] = false;
	}
	for (int i = 0; i < column_len; i++)
	{
		a = 1 << i;
		duplicate[i] = true;
		unordered_map<string, int> temp_map;
		dict.push_back(temp_map);
		vector<Node> temp;
		fd.push_back(temp);
	}
	vector<int> tempInt;
	for (int i = 0; i < column_len; i++)
	{
		tempInt.push_back(0);
		dict[i].insert(pair<string, int>(tempField[i], 0));
	}
	row_len = 1;
	data.push_back(tempInt);
	while (getline(inFile, temp))
	{
		//remove comma before whitespace
		for (int i = 0; i < temp.size() - 1; i++)
		{
			if (temp[i] == ',' && temp[i + 1] == ' ')
			{
				temp[i] = '.';
			}
		}
		tempField = split(temp, ',');
		vector<int> tempInt;
		for (int i = 0; i < column_len; i++)
		{
			Attribute a = 1 << i;
			if (dict[i].find(tempField[i]) != dict[i].end())
			{
				int temp = dict[i][tempField[i]];
				duplicate[i] = false;
				tempInt.push_back(temp);
			}
			else
			{
				int t = dict[i].size();
				tempInt.push_back(t);
				dict[i].insert(pair<string, int>(tempField[i], t));
			}
		}
		data.push_back(tempInt);
		row_len++;
	}
	inFile.close();

	for (int i = 0; i < column_len; ++i)
	{
		if (duplicate[i])
		{
			unique_attrs.insert(1 << i);
		}
	}
	delete duplicate;
}

void DFD::solve(string outputFP)
{
	Attribute attr = 1;
	for (int i = 0; i < column_len; ++i)
	{
		attr = 1 << i;
		if (unique_attrs.find(attr) != unique_attrs.end())
		{
			for (int j = 0; j < column_len; ++j)
			{
				if (i == j) continue;
				fd[j].push_back(attr);
			}
			continue;
		}
		attrs.push_back(attr);
	}
	if (!attrs.empty())
	{
		for (int i = 0; i < column_len; ++i)
		{
			attr_solver = new AttrDFD(this);
			for (auto it2 = attrs.begin(); it2 != attrs.end(); ++it2)
			{
				if (*it2 != 1 << i)
				{
					attr_solver->attrs.push_back(*it2);
				}
			}
			Set result = findLHSs(1 << i);
			if (!result.empty())
			{
				for (auto re = result.begin(); re != result.end(); ++re)
				{
					fd[i].push_back(*re);
				}
			}
			delete attr_solver;
		}
	}
	output(outputFP);
}

Set DFD::findLHSs(Attribute attr)
{
	Set seeds;
	for (auto it : attr_solver->attrs)
	{
		seeds.insert(it);
	}
	while (!seeds.empty())
	{
		for (auto it = seeds.begin(); it != seeds.end(); ++it)
		{
			Node n = *it;
			int old_n = -1;
			do
			{
				if (attr_solver->isVisited(n))
				{
					if (attr_solver->isCandidate(n))
					{
						if (attr_solver->isDependency(n))
						{
							if (attr_solver->isMinimal(n))
							{
								attr_solver->addDependency(n);
							}
						}
						else
						{
							if (attr_solver->isMaximal(n))
							{
								attr_solver->addNonDependency(n);
							}
						}
					}
				}
				else
				{
					attr_solver->inferCategory(n);
					if (attr_solver->getCategory(n) == Category::none)
					{
						if (attr_solver->computePartitions(n, old_n, attr) - partitions_len[n + attr] ==
							attr_solver->getPartition(n, -1) - partitions_len[n])
						{
							attr_solver->addDepCandidate(n);
						}
						else
						{
							attr_solver->addNonDepCandidate(n);
						}
					}
				}
				old_n = n;
				n = attr_solver->pickNextNode(n);
			} while (n);
		}
		seeds = attr_solver->generateNextSeeds();
	}
	return attr_solver->dependencies;
}

void DFD::output(string outputFP)
{
	int total_size = 0;
	int current_size = 0;
	for (int i = 0; i < fd.size(); ++i)
	{
		total_size += fd[i].size();
	}
	int * l = new int[total_size];
	int * r = new int[total_size];
	for (int i = 0; i < total_size; ++i)
	{
		l[i] = r[i] = 0;
	}
	for (int i = 0; i < fd.size(); ++i)
	{
		for (int j = 0; j < fd[i].size(); ++j)
		{
			int lt = fd[i][j];
			int ct = current_size - 1;
			while (ct != -1 && compare(lt, l[ct]))
			{
				l[ct + 1] = l[ct];
				r[ct + 1] = r[ct];
				--ct;
			}
			l[ct + 1] = lt;
			r[ct + 1] = i;
			++current_size;
		}
	}
	ofstream output;
	output.open(outputFP);
	Attribute a = 1;
	int k = 0;
	for (int i = 0; i < total_size; ++i)
	{
		for (int j = 0; j < column_len; ++j)
		{
			Attribute a = 1 << j;
			if ((a & l[i]) == a)
			{
				output << j + 1 << ' ';
			}
		}
		output << "-> " << r[i] + 1 << endl;
	}
}

bool DFD::compare(int a, int b)
{
	for (int i = 0; i < column_len; ++i)
	{
		if (a == 0 && b != 0)
			return true;
		else if (b == 0 && a != 0)
			return false;
		if (a % 2 == 1 && b % 2 != 1)
			return true;
		else if (b % 2 == 1 && a % 2 != 1)
			return false;
		a >>= 1;
		b >>= 1;
	}
	return false;
}

bool AttrDFD::isVisited(Node n)
{
	return visited[n];
}

bool AttrDFD::isCandidate(Node n)
{
	return candidate_dependency[n] || candidate_non_dependency[n];
}

bool AttrDFD::isDependency(Node n)
{
	return dependency[n] || candidate_dependency[n] || minimal_dependency[n];
}


bool AttrDFD::isNonDependency(Node n)
{
	return non_dependency[n] || candidate_non_dependency[n] || maximal_non_dependency[n];
}

void AttrDFD::addDependency(Node n)
{
	candidate_dependency[n] = false;
	minimal_dependency[n] = true;
	dependencies.insert(n);
}

void AttrDFD::addNonDependency(Node n)
{
	candidate_non_dependency[n] = false;
	maximal_non_dependency[n] = true;
	non_dependencies.insert(n);
}

void AttrDFD::addDepCandidate(Node n)
{
	candidate_dependency[n] = true;
}

void AttrDFD::addNonDepCandidate(Node n)
{
	candidate_non_dependency[n] = true;
}

void AttrDFD::removeDepCandidate(Node n)
{
	candidate_dependency[n] = false;
	dependency[n] = true;
}

void AttrDFD::removeNonDepCandidate(Node n)
{
	candidate_non_dependency[n] = false;
	non_dependency[n] = true;
}

bool AttrDFD::isMinimal(Node n)
{
	for (auto it = attrs.begin(); it != attrs.end(); ++it)
	{
		if (*it == n) continue;
		Node subset = (*it) ^ n;
		if (subset > n)
			continue;
		if (isVisited(subset))
		{
			if (isDependency(subset))
			{
				removeDepCandidate(n);
				return false;
			}
		}
		else
		{
			return false;
		}
	}
	return true;
}

bool AttrDFD::isMaximal(Node n)
{
	for (auto it = attrs.begin(); it != attrs.end(); ++it)
	{
		if (*it == n) continue;
		Node superset = (*it) ^ n;
		if (superset < n)
			continue;
		if (isVisited(superset))
		{
			if (isNonDependency(superset))
			{
				removeNonDepCandidate(n);
				return false;
			}
		}
		else
		{
			return false;
		}
	}
	return true;
}

void AttrDFD::updateDependencyType(Node n, Category before)
{
	if (before == Category::candidate_dependency)
	{
		candidate_dependency[n] = false;
		minimal_dependency[n] = true;
	}
	else if (before == Category::candidate_non_dependency)
	{
		candidate_non_dependency[n] = false;
		maximal_non_dependency[n] = true;
	}
	else
	{
		throw "Invalid Dependency Type Update!";
	}
}

void AttrDFD::inferCategory(Node n) // superset a != b && a & b == b, 只考虑对于minimal的超集， isvisited=true
{
	visited[n] = true;
	if (!minimal_dependency.empty())
	{
		for (auto it = minimal_dependency.begin(); it != minimal_dependency.end(); ++it)
		{
			if (!it->second) continue;
			if (it->first != n && ((it->first & n) == it->first))
			{
				dependency[n] = true;
			}
		}
		for (auto it : candidate_dependency)
		{
			if (!it.second) continue;
			if (it.first != n && ((it.first & n) == it.first))
			{
				dependency[n] = true;
			}
		}
	}
	if (!maximal_non_dependency.empty())
	{
		for (auto it = maximal_non_dependency.begin(); it != maximal_non_dependency.end(); ++it)
		{
			if (!it->second) continue;
			if (it->first != n && ((it->first & n) == n))
			{
				non_dependency[n] = true;
			}
		}
		for (auto it : candidate_non_dependency)
		{
			if (!it.second) continue;
			if (it.first != n && ((it.first & n) == n))
			{
				non_dependency[n] = true;
			}
		}
	}
}

int AttrDFD::computePartitions(Node n, Node old_n, Attribute a)
{
	if (super->partitions_checked[n + a])
		return super->partitions[n + a].size();

	int lenA, lenB;
	int * T;
	vector< vector<int> > S;
	vector<int> tmpVec;

	lenA = getPartition(n, old_n);
	lenB = getPartition(a, -1);
	T = new int[super->row_len];
	S = vector< vector<int> >(lenA);
	tmpVec = vector<int>();

	for (int i = 0; i< super->row_len; ++i)
	{
		T[i] = -1;
	}
	for (int i = 0; i < lenA; ++i) {
		for (auto t : super->partitions[n][i]) {
			T[t] = i;
		}
		S.push_back(tmpVec);
	}

	for (int i = 0; i < lenB; ++i) {
		for (auto t : super->partitions[a][i]) {
			if (T[t] >= 0) {
				S[T[t]].push_back(t);
			}
		}
		for (auto t : super->partitions[a][i]) {
			if (T[t] >= 0) {
				int s = S[T[t]].size();
				if (s >= 2) {
					super->partitions[a + n].push_back(S[T[t]]);
					super->partitions_len[a + n] += s;
				}
				S[T[t]] = tmpVec;
			}
		}
	}
	super->partitions_checked[n + a] = true;
	return super->partitions[n + a].size();
}

int AttrDFD::getPartition(Node n, Node old_n)
{
	if (super->partitions_checked[n]) {
		return super->partitions[n].size();
	}

	int column_index;
	int tmpLen;
	vector< vector<int> > tmpVec;

	if (old_n != -1 && (old_n & n) == old_n)
		return computePartitions(old_n, -1, n - old_n);

	for (auto it : attrs)
	{
		if (it < n && ((it & n) != 0) && super->partitions_checked[n - it])
			return computePartitions(n - it, -1, it);
	}

	Attribute a = 1;
	for (int i = 0; i < super->column_len; ++i)
	{
		a = 1 << i;
		if (a < n && ((a & n) != 0))
		{
			return computePartitions(n - a, -1, a);
		}
		else if (a == n)
		{
			column_index = i;
			break;
		}
	}

	// first, use unordered_map to do the partition
	tmpLen = 0;
	for (int i = 0; i < super->row_len; ++i) {
		if (super->data[i][column_index] < tmpLen) {
			tmpVec[super->data[i][column_index]].push_back(i);
		}
		else {
			vector<int> a;
			a.push_back(i);
			tmpVec.push_back(a);
			++tmpLen;
		}
	}

	// then, drop the set that length equals to 1
	for (auto t : tmpVec) {
		int st = t.size();
		if (st != 1) {
			super->partitions[n].push_back(t);
			super->partitions_len[n] += st;
		}
	}
	super->partitions_checked[n] = true;
	return super->partitions[n].size();
}

void AttrDFD::addTrace(Node n)
{
	trace.push_back(n);
}

Node AttrDFD::getTrace()
{
	Node n = trace.back();
	trace.pop_back();
	return n;
}

vector<string> split(string raw, char delim)
{
	vector<string> row;
	int i = 0;
	int point = 0;
	for (; i < raw.length(); ++i)
	{
		if (raw[i] == ',')
		{
			row.push_back(raw.substr(point, i - point));
			point = i + 1;
		}
	}
	row.push_back(raw.substr(point, i - point));
	return row;
}
