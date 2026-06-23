CXX ?= g++
CXXFLAGS := -std=c++17 -O2 -Wall -Wextra -pedantic
LDFLAGS := -lpsapi

ALG_DIR := algorithms
DATA_DIR := data
SCRIPT_DIR := scripts

BRUTE_SRC := $(ALG_DIR)/brute-force.cpp
DP_SRC := $(ALG_DIR)/dynamic-programming.cpp
GREEDY1_SRC := $(ALG_DIR)/greedy1.cpp
GREEDY2_SRC := $(ALG_DIR)/greedy2.cpp
GENERAL_SRC := general.cpp

BRUTE_EXE := $(ALG_DIR)/brute-force.exe
DP_EXE := $(ALG_DIR)/dynamic-programming.exe
GREEDY1_EXE := $(ALG_DIR)/greedy1.exe
GREEDY2_EXE := $(ALG_DIR)/greedy2.exe
GENERAL_EXE := general.exe

INPUTS_DIR := $(DATA_DIR)/inputs
OUTPUTS_DIR := $(DATA_DIR)/outputs
MEASUREMENTS_DIR := $(DATA_DIR)/measurements

.PHONY: all build run clean

all: build run

build: $(BRUTE_EXE) $(DP_EXE) $(GREEDY1_EXE) $(GREEDY2_EXE) $(GENERAL_EXE)

$(BRUTE_EXE): $(BRUTE_SRC)
	$(CXX) $(CXXFLAGS) $< -o $@

$(DP_EXE): $(DP_SRC)
	$(CXX) $(CXXFLAGS) $< -o $@

$(GREEDY1_EXE): $(GREEDY1_SRC)
	$(CXX) $(CXXFLAGS) $< -o $@

$(GREEDY2_EXE): $(GREEDY2_SRC)
	$(CXX) $(CXXFLAGS) $< -o $@

$(GENERAL_EXE): $(GENERAL_SRC)
	$(CXX) $(CXXFLAGS) $< -o $@ $(LDFLAGS)

run: build
	./$(GENERAL_EXE) --inputs $(INPUTS_DIR) --outputs $(OUTPUTS_DIR) --measurements $(MEASUREMENTS_DIR) --brute $(BRUTE_EXE) --dp $(DP_EXE) --greedy1 $(GREEDY1_EXE) --greedy2 $(GREEDY2_EXE)

clean:
	del /Q $(ALG_DIR)\*.exe 2>NUL
	del /Q $(GENERAL_EXE) 2>NUL
	del /Q $(MEASUREMENTS_DIR)\*.csv 2>NUL
	del /Q $(MEASUREMENTS_DIR)\*.stderr.txt 2>NUL
	del /Q $(OUTPUTS_DIR)\brute\*.txt 2>NUL
	del /Q $(OUTPUTS_DIR)\dp\*.txt 2>NUL
	del /Q $(OUTPUTS_DIR)\greedy1\*.txt 2>NUL
	del /Q $(OUTPUTS_DIR)\greedy2\*.txt 2>NUL