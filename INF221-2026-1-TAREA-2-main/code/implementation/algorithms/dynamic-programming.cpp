#include <algorithm>
#include <cstddef>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

using namespace std;

//Me falta comentaaaaaar
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

static inline int idx(int m, int e, int E) {
    return m * (E + 1) + e;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n = 0, M = 0, E = 0;
    if (!(cin >> n >> M >> E)) {
        return 0;
    }

    vector<vector<Option>> groups(n);

    for (int i = 0; i < n; ++i) {
        string animeName;
        int q = 0;
        long long bonus = 0;
        cin >> animeName >> q >> bonus;

        vector<Chapter> chapters;
        chapters.resize(q);
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

        groups[i] = options;
    }

    const long long NEG = -(1LL << 60);
    vector<long long> dp((M + 1) * (E + 1), NEG);
    dp[idx(0, 0, E)] = 0;

    int reachableM = 0;
    int reachableE = 0;

    for (int i = 0; i < n; ++i) {
        const vector<Option>& options = groups[i];

        int groupMaxT = 0;
        int groupMaxC = 0;
        for (std::size_t k = 0; k < options.size(); ++k) {
            if (options[k].t > groupMaxT) groupMaxT = options[k].t;
            if (options[k].c > groupMaxC) groupMaxC = options[k].c;
        }

        int nextReachableM = std::min(M, reachableM + groupMaxT);
        int nextReachableE = std::min(E, reachableE + groupMaxC);

        vector<long long> ndp = dp;

        for (std::size_t k = 1; k < options.size(); ++k) {
            const Option& opt = options[k];

            for (int m = nextReachableM; m >= opt.t; --m) {
                int prevM = m - opt.t;
                if (prevM > reachableM) continue;

                for (int e = nextReachableE; e >= opt.c; --e) {
                    int prevE = e - opt.c;
                    if (prevE > reachableE) continue;

                    long long base = dp[idx(prevM, prevE, E)];
                    if (base == NEG) continue;

                    long long candidate = base + opt.value;
                    long long& cur = ndp[idx(m, e, E)];
                    if (candidate > cur) cur = candidate;
                }
            }
        }

        dp = ndp;
        reachableM = nextReachableM;
        reachableE = nextReachableE;
    }

    long long ans = 0;
    for (int m = 0; m <= M; ++m) {
        for (int e = 0; e <= E; ++e) {
            ans = std::max(ans, dp[idx(m, e, E)]);
        }
    }

    cout << ans << '\n';
    return 0;
}
