#include <algorithm>
#include <iostream>
#include <string>
#include <vector>

using namespace std;

/*
En este algoritmo greedy se construyen distintas opciones para cada anime,
considerando ver distintos números de capítulos consecutivos desde el inicio.

Luego, todas estas opciones se ordenan según un criterio local de
satisfacción por energía (valor / energía), priorizando las que entregan
más valor por cada unidad de energía.

Finalmente, se recorren en ese orden y se selecciona una opción por anime
solo si no se ha elegido antes y si cabe dentro de las restricciones de
tiempo (M) y energía (E).

Este programa se compila junto a los demás algoritmos en 'general.cpp' con
los casos de prueba generados por 'testcases_generator'
*/

struct Chapter {
    int t = 0;
    int c = 0;
    long long v = 0;
};

struct Option {
    int animeId = -1;
    int prefixLen = 0;
    int t = 0;
    int c = 0;
    long long value = 0;
    long double ratio = 0.0L;
};

static inline bool betterOption(const Option& a, const Option& b) {
    if (a.ratio != b.ratio) return a.ratio > b.ratio;
    if (a.value != b.value) return a.value > b.value;
    if (a.c != b.c) return a.c < b.c;
    if (a.t != b.t) return a.t < b.t;
    if (a.prefixLen != b.prefixLen) return a.prefixLen < b.prefixLen;
    return a.animeId < b.animeId;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n = 0, M = 0, E = 0;
    if (!(cin >> n >> M >> E)) {
        return 0;
    }

    vector<Option> options;
    options.reserve(7000); // suficiente para la cota del enunciado (Q <= 700)

    for (int i = 0; i < n; ++i) {
        string animeName;
        int q = 0;
        long long bonus = 0;
        cin >> animeName >> q >> bonus;

        vector<Chapter> chapters(q);
        for (int j = 0; j < q; ++j) {
            cin >> chapters[j].t >> chapters[j].c >> chapters[j].v;
        }

        int prefT = 0;
        int prefC = 0;
        long long prefV = 0;

        for (int len = 1; len <= q; ++len) {
            prefT += chapters[len - 1].t;
            prefC += chapters[len - 1].c;
            prefV += chapters[len - 1].v;

            long long totalValue = prefV;
            if (len == q) {
                totalValue += bonus;
            }

            Option opt;
            opt.animeId = i;
            opt.prefixLen = len;
            opt.t = prefT;
            opt.c = prefC;
            opt.value = totalValue;
            opt.ratio = static_cast<long double>(totalValue) / static_cast<long double>(prefC);
            options.push_back(opt);
        }
    }

    sort(options.begin(), options.end(), betterOption);

    vector<bool> usedAnime(n, false);
    long long totalValue = 0;
    int usedM = 0;
    int usedE = 0;

    for (const Option& opt : options) {
        if (usedAnime[opt.animeId]) {
            continue;
        }
        if (usedM + opt.t > M) {
            continue;
        }
        if (usedE + opt.c > E) {
            continue;
        }

        usedAnime[opt.animeId] = true;
        usedM += opt.t;
        usedE += opt.c;
        totalValue += opt.value;
    }

    cout << totalValue << '\n';
    return 0;
}
