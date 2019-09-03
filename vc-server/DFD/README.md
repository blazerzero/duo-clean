# Database-Functional-Dependency-Mining-Algorithms
> Author of TANE: [Qianrui Zhang](https://github.com/owen6314)  
> Author of DFD: [Jinghan Gao](https://github.com/getterk96)

## Usage
Mining functional dependencies from database raw data, with TANE and DFD, two algorithms included.

### TANE
In **main.cpp**, change

	TANE("input file path")

to your own absolute path.

Compile the file then.

	g++ FD.cpp main.cpp TANE.cpp -std=c++11 -Ofast -o digger

Run the digger.

	./digger

### DFD 
In **main.cpp**, change

	open("input file path")

to your own absolute path.

Compile the file then.

	g++ DFD.cpp main.cpp -std=c++11 -Ofast -o digger

Run the digger.

	./digger


## Test Result of TANE
|data size|searching time|  
|-|-|  
|100,000|2.423s|
## Test Result of DFD 
|data size|searching time|  
|-|-|  
|100,000|9.982s|
