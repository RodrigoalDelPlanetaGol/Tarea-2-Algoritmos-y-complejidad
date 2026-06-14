#define NOMINMAX
#include <windows.h>
#include <psapi.h>

#include <algorithm>
#include <chrono>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

/*
 * INF-221 - Tarea 2: AniMarathon
 * Programa general de medición para Windows/MinGW.
 *
 * Qué hace:
 *   - Recorre los .txt dentro de una carpeta de inputs.
 *   - Ejecuta cada algoritmo como proceso independiente.
 *   - Guarda la salida de cada algoritmo en data/outputs/<algoritmo>/.
 *   - Registra tiempo y memoria en data/measurements/measurements.csv.
 *
 * Ventaja de esta versión:
 *   - No usa std::filesystem.
 *   - Evita los problemas de compilación que dan algunas versiones de MinGW.
 *
 * Compilación sugerida:
 *   g++ -std=c++17 -O2 general.cpp -o general.exe -lpsapi
 */

using namespace std;

struct RunResult {
    bool launched = false;
    bool finished = false;
    int returnCode = -1;
    long long timeMs = -1;
    long long memoryKb = -1;
    string stdoutText;
    string stderrText;
};

static string normalizeSlashes(string s) {
    replace(s.begin(), s.end(), '/', '\\');
    return s;
}

static string joinPath(const string& a, const string& b) {
    if (a.empty()) return normalizeSlashes(b);
    string left = normalizeSlashes(a);
    string right = normalizeSlashes(b);
    if (!left.empty() && left.back() != '\\') {
        left.push_back('\\');
    }
    return left + right;
}

static string fileStem(const string& path) {
    string normalized = normalizeSlashes(path);
    size_t slash = normalized.find_last_of('\\');
    string name = (slash == string::npos) ? normalized : normalized.substr(slash + 1);
    size_t dot = name.find_last_of('.');
    if (dot == string::npos) return name;
    return name.substr(0, dot);
}

static bool ensureDirRecursive(const string& rawPath) {
    string path = normalizeSlashes(rawPath);
    if (path.empty()) return true;

    string current;
    size_t i = 0;

    // Manejo simple de rutas tipo C:\...
    if (path.size() >= 3 && path[1] == ':' && path[2] == '\\') {
        current = path.substr(0, 3);
        i = 3;
    }

    for (; i < path.size(); ++i) {
        char ch = path[i];
        if (ch == '\\') {
            if (!current.empty()) {
                if (!CreateDirectoryA(current.c_str(), nullptr)) {
                    DWORD err = GetLastError();
                    if (err != ERROR_ALREADY_EXISTS) {
                        return false;
                    }
                }
            }
            if (current.empty() || current.back() != '\\') {
                current.push_back('\\');
            }
        } else {
            current.push_back(ch);
        }
    }

    if (!current.empty()) {
        if (!CreateDirectoryA(current.c_str(), nullptr)) {
            DWORD err = GetLastError();
            if (err != ERROR_ALREADY_EXISTS) {
                return false;
            }
        }
    }
    return true;
}

static vector<string> listTxtFiles(const string& dir) {
    vector<string> files;
    string pattern = joinPath(dir, "*.txt");

    WIN32_FIND_DATAA fd{};
    HANDLE hFind = FindFirstFileA(pattern.c_str(), &fd);
    if (hFind == INVALID_HANDLE_VALUE) {
        return files;
    }

    do {
        if (!(fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
            files.push_back(joinPath(dir, fd.cFileName));
        }
    } while (FindNextFileA(hFind, &fd));

    FindClose(hFind);
    sort(files.begin(), files.end());
    return files;
}

static bool writeTextFile(const string& path, const string& text) {
    ofstream out(path, ios::binary | ios::trunc);
    if (!out) return false;
    out << text;
    return true;
}

static string readTextFile(const string& path) {
    ifstream in(path, ios::binary);
    if (!in) return "";
    stringstream ss;
    ss << in.rdbuf();
    return ss.str();
}

static RunResult runProcessWindows(const string& exe,
                                   const string& inputFile,
                                   const string& stdoutFile,
                                   const string& stderrFile) {
    RunResult result;

    HANDLE hInput = CreateFileA(inputFile.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr,
                                OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (hInput == INVALID_HANDLE_VALUE) {
        return result;
    }

    HANDLE hOut = CreateFileA(stdoutFile.c_str(), GENERIC_WRITE, 0, nullptr,
                              CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (hOut == INVALID_HANDLE_VALUE) {
        CloseHandle(hInput);
        return result;
    }

    HANDLE hErr = CreateFileA(stderrFile.c_str(), GENERIC_WRITE, 0, nullptr,
                              CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (hErr == INVALID_HANDLE_VALUE) {
        CloseHandle(hInput);
        CloseHandle(hOut);
        return result;
    }

    STARTUPINFOA si{};
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdInput = hInput;
    si.hStdOutput = hOut;
    si.hStdError = hErr;

    PROCESS_INFORMATION pi{};

    string cmd = "\"" + exe + "\"";
    vector<char> mutableCmd(cmd.begin(), cmd.end());
    mutableCmd.push_back('\0');

    auto start = chrono::steady_clock::now();
    BOOL ok = CreateProcessA(
        nullptr,
        mutableCmd.data(),
        nullptr,
        nullptr,
        TRUE,
        0,
        nullptr,
        nullptr,
        &si,
        &pi
    );

    result.launched = (ok != FALSE);
    if (!ok) {
        CloseHandle(hInput);
        CloseHandle(hOut);
        CloseHandle(hErr);
        return result;
    }

    WaitForSingleObject(pi.hProcess, INFINITE);
    auto end = chrono::steady_clock::now();

    DWORD exitCode = 0;
    GetExitCodeProcess(pi.hProcess, &exitCode);
    result.returnCode = static_cast<int>(exitCode);
    result.timeMs = chrono::duration_cast<chrono::milliseconds>(end - start).count();
    result.finished = true;

    PROCESS_MEMORY_COUNTERS pmc{};
    if (GetProcessMemoryInfo(pi.hProcess, &pmc, sizeof(pmc))) {
        result.memoryKb = static_cast<long long>(pmc.PeakWorkingSetSize / 1024ULL);
    }

    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    CloseHandle(hInput);
    CloseHandle(hOut);
    CloseHandle(hErr);

    result.stdoutText = readTextFile(stdoutFile);
    result.stderrText = readTextFile(stderrFile);
    return result;
}

static string getArgValue(int argc, char* argv[], const string& flag, const string& defaultValue) {
    for (int i = 1; i < argc; ++i) {
        if (flag == argv[i] && i + 1 < argc) {
            return argv[i + 1];
        }
    }
    return defaultValue;
}

int main(int argc, char* argv[]) {
    string inputsDir = getArgValue(argc, argv, "--inputs", "data/inputs");
    string outputsDir = getArgValue(argc, argv, "--outputs", "data/outputs");
    string measurementsDir = getArgValue(argc, argv, "--measurements", "data/measurements");

    string bruteExe = getArgValue(argc, argv, "--brute", "algorithms/brute-force.exe");
    string dpExe = getArgValue(argc, argv, "--dp", "algorithms/dynamic-programming.exe");
    string greedy1Exe = getArgValue(argc, argv, "--greedy1", "algorithms/greedy1.exe");
    string greedy2Exe = getArgValue(argc, argv, "--greedy2", "algorithms/greedy2.exe");

    if (!ensureDirRecursive(outputsDir) || !ensureDirRecursive(measurementsDir)) {
        cerr << "No se pudieron crear las carpetas de salida/medición.\n";
        return 1;
    }

    const vector<pair<string, string>> algorithms = {
        {"brute", bruteExe},
        {"dp", dpExe},
        {"greedy1", greedy1Exe},
        {"greedy2", greedy2Exe}
    };

    for (const auto& algo : algorithms) {
        if (!ensureDirRecursive(joinPath(outputsDir, algo.first))) {
            cerr << "No se pudo crear la carpeta de salida para " << algo.first << '\n';
            return 1;
        }
    }

    vector<string> inputFiles = listTxtFiles(inputsDir);
    if (inputFiles.empty()) {
        cerr << "No se encontraron archivos .txt en: " << inputsDir << '\n';
        return 1;
    }

    for (const auto& algo : algorithms) {
        if (GetFileAttributesA(algo.second.c_str()) == INVALID_FILE_ATTRIBUTES) {
            cerr << "No existe el ejecutable de " << algo.first << ": " << algo.second << '\n';
            return 1;
        }
    }

    string csvPath = joinPath(measurementsDir, "measurements.csv");
    ofstream csv(csvPath, ios::out | ios::trunc);
    if (!csv) {
        cerr << "No se pudo crear: " << csvPath << '\n';
        return 1;
    }

    csv << "case,algorithm,time_ms,memory_kb,return_code,ok,output_file,stderr_file\n";

    cout << "Inputs: " << inputsDir << '\n';
    cout << "Outputs: " << outputsDir << '\n';
    cout << "Measurements: " << measurementsDir << '\n';
    cout << "Casos encontrados: " << inputFiles.size() << "\n\n";

    for (const string& inputFile : inputFiles) {
        string caseName = fileStem(inputFile);
        cout << "== " << caseName << " ==\n";

        for (const auto& algo : algorithms) {
            string outFile = joinPath(joinPath(outputsDir, algo.first), caseName + ".txt");
            string errFile = joinPath(measurementsDir, caseName + "_" + algo.first + ".stderr.txt");

            RunResult res = runProcessWindows(algo.second, inputFile, outFile, errFile);

            writeTextFile(outFile, res.stdoutText);
            writeTextFile(errFile, res.stderrText);

            bool ok = res.launched && res.finished && res.returnCode == 0;
            csv << caseName << ','
                << algo.first << ','
                << res.timeMs << ','
                << res.memoryKb << ','
                << res.returnCode << ','
                << (ok ? 1 : 0) << ','
                << outFile << ','
                << errFile << '\n';

            cout << "  " << algo.first << ": ";
            if (!res.launched) {
                cout << "no se pudo ejecutar";
            } else if (!res.finished) {
                cout << "no terminó";
            } else {
                if (res.stdoutText.empty()) {
                    cout << "<sin salida>";
                } else {
                    cout << res.stdoutText;
                }
            }
            cout << " [" << res.timeMs << " ms, " << res.memoryKb << " KB, rc=" << res.returnCode << "]\n";
        }

        cout << '\n';
    }

    cout << "CSV generado en: " << csvPath << '\n';
    return 0;
}
