#define NOMINMAX
#include <windows.h>
#include <psapi.h>

#include <algorithm>
#include <chrono>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

/*
 Este programa actúa como el controlador del proceso experimental, ya que 
 recorre todos los casos de prueba generados, ejecuta cada uno de los algoritmos 
 implementados (brute-force, programación dinámica y los dos greedy) sobre dichos inputs,
 guarda sus salidas en las carpetas correspondientes y registra métricas como tiempo de
 ejecución, uso de memoria y código de retorno en un archivo measurements.csv, el cual 
 luego se utiliza para el análisis y generación de gráficos; además, 
 evita ejecutar brute-force en instancias grandes para no incurrir en tiempos excesivos.
 Para compilar, se debe abrir la terminal en la carpeta 'implementations\' y ejecutar
 el comando 'make' para ejecutar el makefile.
 */

using std::string;
using std::vector;

struct RunResult {
    bool launched = false;
    bool finished = false;
    int returnCode = -1;
    long long timeMs = -1;
    long long memoryKb = -1;
    string stdoutText;
    string stderrText;
};

struct CaseMeta {
    int n = 0;
    int M = 0;
    int E = 0;
    int totalChapters = 0;
    long long totalDuration = 0;
    long long totalEnergy = 0;
    bool ok = false;
};

static string normalizeSlashes(string s) {
    std::replace(s.begin(), s.end(), '/', '\\');
    return s;
}

static string joinPath(const string& a, const string& b) {
    if (a.empty()) return normalizeSlashes(b);
    string left = normalizeSlashes(a);
    string right = normalizeSlashes(b);
    if (!left.empty() && left.back() != '\\') left.push_back('\\');
    return left + right;
}

static string fileStem(const string& path) {
    string p = normalizeSlashes(path);
    size_t slash = p.find_last_of('\\');
    string name = (slash == string::npos) ? p : p.substr(slash + 1);
    size_t dot = name.find_last_of('.');
    return (dot == string::npos) ? name : name.substr(0, dot);
}

static string getExecutableDir() {
    char buffer[MAX_PATH] = {0};
    DWORD len = GetModuleFileNameA(nullptr, buffer, MAX_PATH);
    string full(buffer, buffer + len);
    size_t slash = full.find_last_of("\\/");
    if (slash == string::npos) return string();
    return full.substr(0, slash);
}

static string resolvePath(const string& baseDir, const string& path) {
    string p = normalizeSlashes(path);
    if (p.size() >= 2 && p[1] == ':') return p;
    if (!p.empty() && (p[0] == '\\' || p[0] == '/')) return p;
    if (baseDir.empty()) return p;
    return joinPath(baseDir, p);
}

static bool ensureDirRecursive(const string& rawPath) {
    string path = normalizeSlashes(rawPath);
    if (path.empty()) return true;

    vector<string> parts;
    size_t start = 0;
    for (size_t i = 0; i <= path.size(); ++i) {
        if (i == path.size() || path[i] == '\\') {
            parts.push_back(path.substr(start, i - start));
            start = i + 1;
        }
    }

    string current;
    size_t idx = 0;
    if (!parts.empty() && parts[0].size() == 2 && parts[0][1] == ':') {
        current = parts[0] + "\\";
        idx = 1;
    }

    for (; idx < parts.size(); ++idx) {
        const string& part = parts[idx];
        if (part.empty()) continue;
        if (!current.empty() && current.back() != '\\') current.push_back('\\');
        current += part;
        if (!CreateDirectoryA(current.c_str(), nullptr)) {
            DWORD err = GetLastError();
            if (err != ERROR_ALREADY_EXISTS) return false;
        }
    }
    return true;
}

static vector<string> listTxtFiles(const string& dir) {
    vector<string> files;
    string pattern = joinPath(dir, "*.txt");

    WIN32_FIND_DATAA fd{};
    HANDLE hFind = FindFirstFileA(pattern.c_str(), &fd);
    if (hFind == INVALID_HANDLE_VALUE) return files;

    do {
        if (!(fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
            files.push_back(joinPath(dir, fd.cFileName));
        }
    } while (FindNextFileA(hFind, &fd));

    FindClose(hFind);
    std::sort(files.begin(), files.end());
    return files;
}

static bool writeTextFile(const string& path, const string& text) {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) return false;
    out << text;
    return true;
}

static string readTextFile(const string& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) return "";
    std::stringstream ss;
    ss << in.rdbuf();
    return ss.str();
}

static bool readCaseMetadata(const string& inputFile, CaseMeta& meta) {
    std::ifstream in(inputFile);
    if (!in) return false;

    string animeName;
    int q = 0;
    long long b = 0;
    int t = 0, c = 0;
    long long v = 0;

    if (!(in >> meta.n >> meta.M >> meta.E)) return false;

    meta.totalChapters = 0;
    meta.totalDuration = 0;
    meta.totalEnergy = 0;

    for (int i = 0; i < meta.n; ++i) {
        if (!(in >> animeName >> q >> b)) return false;
        meta.totalChapters += q;
        for (int j = 0; j < q; ++j) {
            if (!(in >> t >> c >> v)) return false;
            meta.totalDuration += t;
            meta.totalEnergy += c;
        }
    }

    meta.ok = true;
    return true;
}

static RunResult runProcessWindows(const string& exe,
                                   const string& inputFile,
                                   const string& stdoutFile,
                                   const string& stderrFile) {
    RunResult result;

    SECURITY_ATTRIBUTES sa{};
    sa.nLength = sizeof(sa);
    sa.lpSecurityDescriptor = nullptr;
    sa.bInheritHandle = TRUE;

    HANDLE hInput = CreateFileA(inputFile.c_str(), GENERIC_READ, FILE_SHARE_READ, &sa,
                                OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (hInput == INVALID_HANDLE_VALUE) return result;

    HANDLE hOut = CreateFileA(stdoutFile.c_str(), GENERIC_WRITE, 0, &sa,
                              CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (hOut == INVALID_HANDLE_VALUE) {
        CloseHandle(hInput);
        return result;
    }

    HANDLE hErr = CreateFileA(stderrFile.c_str(), GENERIC_WRITE, 0, &sa,
                              CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (hErr == INVALID_HANDLE_VALUE) {
        CloseHandle(hInput);
        CloseHandle(hOut);
        return result;
    }

    SetHandleInformation(hInput, HANDLE_FLAG_INHERIT, HANDLE_FLAG_INHERIT);
    SetHandleInformation(hOut, HANDLE_FLAG_INHERIT, HANDLE_FLAG_INHERIT);
    SetHandleInformation(hErr, HANDLE_FLAG_INHERIT, HANDLE_FLAG_INHERIT);

    STARTUPINFOA si{};
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdInput = hInput;
    si.hStdOutput = hOut;
    si.hStdError = hErr;

    PROCESS_INFORMATION pi{};

    string quotedExe = "\"" + exe + "\"";
    vector<char> cmdLine(quotedExe.begin(), quotedExe.end());
    cmdLine.push_back('\0');

    auto t0 = std::chrono::steady_clock::now();
    BOOL ok = CreateProcessA(
        nullptr,
        cmdLine.data(),
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
    auto t1 = std::chrono::steady_clock::now();

    DWORD exitCode = 0;
    GetExitCodeProcess(pi.hProcess, &exitCode);
    result.returnCode = static_cast<int>(exitCode);
    result.timeMs = std::chrono::duration_cast<std::chrono::milliseconds>(t1 - t0).count();
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
    for (int i = 1; i + 1 < argc; ++i) {
        if (flag == argv[i]) return argv[i + 1];
    }
    return defaultValue;
}

int main(int argc, char* argv[]) {
    string baseDir = getExecutableDir();

    string inputsDir = resolvePath(baseDir, getArgValue(argc, argv, "--inputs", "data/inputs"));
    string outputsDir = resolvePath(baseDir, getArgValue(argc, argv, "--outputs", "data/outputs"));
    string measurementsDir = resolvePath(baseDir, getArgValue(argc, argv, "--measurements", "data/measurements"));

    string bruteExe = resolvePath(baseDir, getArgValue(argc, argv, "--brute", "algorithms/brute-force.exe"));
    string dpExe = resolvePath(baseDir, getArgValue(argc, argv, "--dp", "algorithms/dynamic-programming.exe"));
    string greedy1Exe = resolvePath(baseDir, getArgValue(argc, argv, "--greedy1", "algorithms/greedy1.exe"));
    string greedy2Exe = resolvePath(baseDir, getArgValue(argc, argv, "--greedy2", "algorithms/greedy2.exe"));

    if (!ensureDirRecursive(outputsDir) || !ensureDirRecursive(measurementsDir)) {
        std::cerr << "No se pudieron crear carpetas de salida/medicion.\n";
        return 1;
    }

    vector<std::pair<string, string>> algos = {
        {"brute", bruteExe},
        {"dp", dpExe},
        {"greedy1", greedy1Exe},
        {"greedy2", greedy2Exe}
    };

    for (const auto& a : algos) {
        if (!ensureDirRecursive(joinPath(outputsDir, a.first))) {
            std::cerr << "No se pudo crear carpeta para " << a.first << "\n";
            return 1;
        }
    }

    vector<string> inputFiles = listTxtFiles(inputsDir);
    if (inputFiles.empty()) {
        std::cerr << "No se encontraron archivos .txt en: " << inputsDir << '\n';
        return 1;
    }

    for (const auto& a : algos) {
        DWORD attr = GetFileAttributesA(a.second.c_str());
        if (attr == INVALID_FILE_ATTRIBUTES) {
            std::cerr << "No existe el ejecutable de " << a.first << ": " << a.second << '\n';
            return 1;
        }
    }

    string csvPath = joinPath(measurementsDir, "measurements.csv");
    std::ofstream csv(csvPath, std::ios::out | std::ios::trunc);
    if (!csv) {
        std::cerr << "No se pudo crear: " << csvPath << '\n';
        return 1;
    }

    csv << "case,algorithm,n,M,E,total_chapters,total_duration,total_energy,time_ms,memory_kb,return_code,ok,skipped,output_file,stderr_file\n";

    std::cout << "Inputs: " << inputsDir << '\n';
    std::cout << "Outputs: " << outputsDir << '\n';
    std::cout << "Measurements: " << measurementsDir << '\n';
    std::cout << "Casos encontrados: " << inputFiles.size() << "\n\n";

    for (const string& inputFile : inputFiles) {
        string caseName = fileStem(inputFile);

        CaseMeta meta;
        bool hasHeader = readCaseMetadata(inputFile, meta);
        bool skipBrute = (!hasHeader || meta.n > 8);

        std::cout << "== " << caseName << " ==\n";

        for (const auto& a : algos) {
            string outFile = joinPath(joinPath(outputsDir, a.first), caseName + ".txt");
            string errFile = joinPath(measurementsDir, caseName + "_" + a.first + ".stderr.txt");

            if (a.first == "brute" && skipBrute) {
                writeTextFile(outFile, "");
                writeTextFile(errFile, "SKIPPED_TOO_LARGE\n");
                csv << caseName << ',' << a.first << ','
                    << meta.n << ',' << meta.M << ',' << meta.E << ','
                    << meta.totalChapters << ',' << meta.totalDuration << ',' << meta.totalEnergy << ','
                    << -1 << ',' << -1 << ',' << -2 << ',' << 0 << ',' << 1 << ','
                    << outFile << ',' << errFile << '\n';
                std::cout << "  brute: omitido por tamano [SKIPPED_TOO_LARGE]\n";
                continue;
            }

            RunResult res = runProcessWindows(a.second, inputFile, outFile, errFile);

            writeTextFile(outFile, res.stdoutText);
            writeTextFile(errFile, res.stderrText);

            bool ok = res.launched && res.finished && res.returnCode == 0;
            csv << caseName << ',' << a.first << ','
                << meta.n << ',' << meta.M << ',' << meta.E << ','
                << meta.totalChapters << ',' << meta.totalDuration << ',' << meta.totalEnergy << ','
                << res.timeMs << ',' << res.memoryKb << ',' << res.returnCode << ','
                << (ok ? 1 : 0) << ',' << 0 << ',' << outFile << ',' << errFile << '\n';

            std::cout << "  " << a.first << ": ";
            if (!res.launched) {
                std::cout << "no se pudo ejecutar";
            } else if (!res.finished) {
                std::cout << "no termino";
            } else if (res.stdoutText.empty()) {
                std::cout << "<sin salida>";
            } else {
                std::cout << res.stdoutText;
            }
            std::cout << " [" << res.timeMs << " ms, " << res.memoryKb << " KB, rc=" << res.returnCode << "]\n";
        }

        std::cout << '\n';
    }

    std::cout << "CSV generado en: " << csvPath << '\n';
    return 0;
}
