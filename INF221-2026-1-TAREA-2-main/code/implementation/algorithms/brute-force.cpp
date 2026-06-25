#include <algorithm>
#include <iostream>
#include <string>
#include <vector>

using namespace std;

/*
Esta implementación realiza una busqueda exhaustiva con poda:
Prueb distintas combinaciones de capitulos que se puedan ver.
Si se completa un anime, se suma un bono adicional.

Se hace una búsqued en profundidad (DFS) para recorrer las combinaciones pero
se aplican podas para no exploraar soluciones que no sirven (como las que se pasan
del tiempo o energía disponible). Además se hace una estimación del valor máximo
posible restante para cortar ramas que no pueden mejorar la mejor solución actual.

Este programa se compila junto a los demás algoritmos en 'general.cpp' con
los casos de prueba generados por 'testcases_generator'
*/

struct Chapter {
    int t = 0;
    int c = 0;
    long long v = 0;
};

struct Option {
    int t = 0;
    int c = 0;
    long long value = 0;
};

struct AnimeOptions {
    vector<Option> options;
};

static int g_n = 0;
static int g_M = 0;
static int g_E = 0;
static vector<AnimeOptions> g_groups;
static vector<long long> g_suffixBest;
static long long g_best = 0;

static void dfs(int idx, int usedM, int usedE, long long current) {
    if (usedM > g_M || usedE > g_E) {
        return;
    }

    if (idx == g_n) {
        if (current > g_best) {
            g_best = current;
        }
        return;
    }

    if (current + g_suffixBest[idx] <= g_best) {
        return;
    }

    const vector<Option>& options = g_groups[idx].options;
    for (const Option& opt : options) {
        dfs(idx + 1, usedM + opt.t, usedE + opt.c, current + opt.value);
    }
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    if (!(cin >> g_n >> g_M >> g_E)) {
        return 0;
    }

    g_groups.assign(g_n, AnimeOptions{});

    for (int i = 0; i < g_n; ++i) {
        string animeName;
        int q = 0;
        long long bonus = 0;
        cin >> animeName >> q >> bonus;

        vector<Chapter> chapters(q);
        for (int j = 0; j < q; ++j) {
            cin >> chapters[j].t >> chapters[j].c >> chapters[j].v;
        }

        vector<Option> options;
        options.reserve(q + 1);

        options.push_back({0, 0, 0}); // no tomar nada del anime

        int prefT = 0;
        int prefC = 0;
        long long prefV = 0;

        for (int j = 0; j < q; ++j) {
            prefT += chapters[j].t;
            prefC += chapters[j].c;
            prefV += chapters[j].v;

            long long totalValue = prefV;
            if (j == q - 1) {
                totalValue += bonus; // bono solo si se completa el anime
            }

            options.push_back({prefT, prefC, totalValue});
        }

        g_groups[i].options = std::move(options);
    }

    g_suffixBest.assign(g_n + 1, 0);
    for (int i = g_n - 1; i >= 0; --i) {
        long long bestHere = 0;
        for (const Option& opt : g_groups[i].options) {
            bestHere = max(bestHere, opt.value);
        }
        g_suffixBest[i] = g_suffixBest[i + 1] + bestHere;
    }

    g_best = 0;
    dfs(0, 0, 0, 0LL);

    cout << g_best << '\n';
    return 0;
}