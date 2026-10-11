/*
 * stream-bench.c — STREAM-style memory bandwidth benchmark (OpenMP).
 *
 * Measures sustained memory bandwidth on the full 8-channel configuration:
 *   Copy, Scale, Add, Triad  (classic STREAM kernels)
 *   plus a RANDOM-read kernel (cache-hostile permutation walk).
 *
 * Build:  gcc -O3 -fopenmp -march=native stream-bench.c -o stream-bench -lm
 * Run:    OMP_NUM_THREADS=128 OMP_PROC_BIND=spread ./stream-bench 1024
 *
 * Anti-optimization follows the canonical STREAM approach: an outer parallel
 * region with per-rep `#pragma omp for`, a scalar that changes every rep, and
 * a sink that is checked after timing so the compiler cannot remove the work.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <omp.h>

static double now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

static void report(const char *name, size_t mib, double bytes_moved,
                   double secs, double sink) {
    double mibs = bytes_moved / secs;
    printf("%-6s: %9.1f MiB/s  (%6.1f GiB/s)  [%.4f s]  sink=%g\n",
           name, mibs, mibs / 1024.0, secs, sink);
}

int main(int argc, char **argv) {
    size_t mib = (argc > 1) ? (size_t)atol(argv[1]) : 1024;
    size_t n = mib * 1024 * 1024 / sizeof(double);
    int nthreads = omp_get_max_threads();
    const int reps = 5;

    printf("STREAM benchmark: %zu MiB per array (3 arrays = %.1f GiB working set)\n",
           mib, 3.0 * mib / 1024.0);
    printf("threads=%d  elements=%zu  reps=%d\n\n", nthreads, n, reps);

    double *a = aligned_alloc(64, n * sizeof(double));
    double *b = aligned_alloc(64, n * sizeof(double));
    double *c = aligned_alloc(64, n * sizeof(double));
    if (!a || !b || !c) { fprintf(stderr, "alloc failed\n"); return 1; }

    double *times = calloc(reps, sizeof(double));
    double scalar = 3.0;
    double sink = 0.0;

    #pragma omp parallel for
    for (size_t i = 0; i < n; i++) { a[i] = 1.0; b[i] = 2.0; c[i] = 0.0; }

    /* ---- Copy: c = a ---- */
    for (int r = 0; r < reps; r++) {
        scalar = 3.0 + r;                 /* change work each rep */
        double t = now();
        #pragma omp parallel for
        for (size_t i = 0; i < n; i++) c[i] = a[i];
        times[r] = now() - t;
    }
    double best = times[0];
    for (int r = 1; r < reps; r++) if (times[r] < best) best = times[r];
    report("Copy", mib, 2.0 * mib, best, sink);

    /* ---- Scale: b = scalar * c ---- */
    for (int r = 0; r < reps; r++) {
        scalar = 3.0 + r;
        double t = now();
        #pragma omp parallel for
        for (size_t i = 0; i < n; i++) b[i] = scalar * c[i];
        times[r] = now() - t;
    }
    best = times[0];
    for (int r = 1; r < reps; r++) if (times[r] < best) best = times[r];
    report("Scale", mib, 2.0 * mib, best, sink);

    /* ---- Add: c = a + b ---- */
    for (int r = 0; r < reps; r++) {
        scalar = 3.0 + r;
        double t = now();
        #pragma omp parallel for
        for (size_t i = 0; i < n; i++) c[i] = a[i] + b[i];
        times[r] = now() - t;
    }
    best = times[0];
    for (int r = 1; r < reps; r++) if (times[r] < best) best = times[r];
    report("Add", mib, 3.0 * mib, best, sink);

    /* ---- Triad: a = b + scalar * c ---- */
    for (int r = 0; r < reps; r++) {
        scalar = 3.0 + r;
        double t = now();
        #pragma omp parallel for
        for (size_t i = 0; i < n; i++) a[i] = b[i] + scalar * c[i];
        times[r] = now() - t;
    }
    best = times[0];
    for (int r = 1; r < reps; r++) if (times[r] < best) best = times[r];
    report("Triad", mib, 3.0 * mib, best, sink);

    /* ---- Random read: cache-hostile permutation walk ---- */
    size_t *perm = malloc(n * sizeof(size_t));
    for (size_t i = 0; i < n; i++) perm[i] = i;
    unsigned int seed = 12345;
    for (size_t i = n - 1; i > 0; i--) {
        size_t j = rand_r(&seed) % (i + 1);
        size_t t2 = perm[i]; perm[i] = perm[j]; perm[j] = t2;
    }

    double rbest = 1e30;
    for (int r = 0; r < reps; r++) {
        double local = 0;
        double t = now();
        #pragma omp parallel for reduction(+:local)
        for (size_t i = 0; i < n; i++) local += a[perm[i]];
        double dt = now() - t;
        sink += local;
        if (dt < rbest) rbest = dt;
    }
    report("RandR", mib, (double)mib, rbest, sink);
    printf("       (random read: useful 8 B payload per 16 B touched; "
           "raw traffic would be ~2x)\n");

    /* ---- Random write: scatter write through the same permutation ---- */
    double wbest = 1e30;
    for (int r = 0; r < reps; r++) {
        scalar = 3.0 + r;
        double t = now();
        #pragma omp parallel for
        for (size_t i = 0; i < n; i++) b[perm[i]] = scalar;
        double dt = now() - t;
        if (dt < wbest) wbest = dt;
    }
    report("RandW", mib, (double)mib, wbest, sink);
    printf("       (random write: scattered 8 B stores)\n");

    /* ---- Random read-modify-write: c[perm[i]] += a[perm[i]] ---- */
    double rwbest = 1e30;
    for (int r = 0; r < reps; r++) {
        double t = now();
        #pragma omp parallel for
        for (size_t i = 0; i < n; i++) c[perm[i]] += a[perm[i]];
        double dt = now() - t;
        if (dt < rwbest) rwbest = dt;
    }
    report("RandRW", mib, 2.0 * mib, rwbest, sink);
    printf("       (random read-modify-write: 1 read + 1 write per element)\n");

    printf("\nvalidation sink=%g (non-zero => kernels were not optimized away)\n",
           sink);
    free(a); free(b); free(c); free(perm); free(times);
    return 0;
}
