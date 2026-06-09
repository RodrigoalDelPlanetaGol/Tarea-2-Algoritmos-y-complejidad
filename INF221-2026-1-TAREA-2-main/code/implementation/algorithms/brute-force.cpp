#include <algorithm>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

using namespace std;

/*
 *   Prueba todas las combinaciones posibles de prefijos válidos de cada anime:
 *     - elegir 0 capítulos
 *     - elegir 1 capítulo
 *     - elegir 2 capítulos
 *     - ...
 *     - elegir q_i capítulos
 *
 * Restricciones:
 *   - Solo se puede tomar un prefijo de cada anime.
 *   - La suma de minutos no puede exceder M.
 *   - La suma de energía no puede exceder E.
 *
 * Esta implementación está pensada para casos pequeños.
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
    long long suffixUpperBound = 0;
};

static inline void fast_io() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
}

int main() {
    fast_io();

    int n = 0, M = 0, E = 0;
    if (!(cin >> n >> M >> E)) {
        return 0;
    }

    vector<AnimeOptions> groups;
    groups.resize(n);

    for (int i = 0; i < n; ++i) {
        string animeName;
        int q = 0;
        long long bonus = 0;
        cin >> animeName >> q >> bonus;

        vector<Chapter> chapters(q);
        for (int j = 0; j < q; ++j) {
            cin >> chapters[j].t >> chapters[j].c >> chapters[j].v;
        }

        vector<Option> options;
        options.resize(q + 1);
        options[0] = {0, 0, 0};

        int prefT = 0;
        int prefC = 0;
        long long prefV = 0;
        for (int j = 0; j < q; ++j) {
            prefT += chapters[j].t;
            prefC += chapters[j].c;
            prefV += chapters[j].v;

            long long totalValue = prefV;
            if (j == q - 1) {
                totalValue += bonus;
            }
            options[j + 1] = {prefT, prefC, totalValue};
        }

        groups[i].options = options;
    }

    // Poda por cota superior: suma de la mejor opción de cada anime restante.
    // No considera recursos, así que es una cota optimista válida.
    vector<long long> suffixBest(n + 1, 0);
    for (int i = n - 1; i >= 0; --i) {
        long long bestHere = 0;
        for (const Option& opt : groups[i].options) {
            bestHere = max(bestHere, opt.value);
        }
        suffixBest[i] = suffixBest[i + 1] + bestHere;
    }

    long long best = 0;

    // DFS exhaustivo con poda.
    // idx: anime actual
    // usedM / usedE: recursos consumidos
    // current: satisfacción acumulada
    auto dfs = [&](auto&& self, int idx, int usedM, int usedE, long long current) -> void {
        if (usedM > M || usedE > E) {
            return;
        }
        if (idx == n) {
            if (current > best) {
                best = current;
            }
            return;
        }

        if (current + suffixBest[idx] <= best) {
            return;
        }

        const vector<Option>& options = groups[idx].options;
        for (const Option& opt : options) {
            self(self, idx + 1, usedM + opt.t, usedE + opt.c, current + opt.value);
        }
    };

    dfs(dfs, 0, 0, 0, 0LL);

    cout << best << '\n';
    return 0;
}
