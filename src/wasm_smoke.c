/*
 * Baseline only: tests WebAssembly toolchain; DOES NOT contain OR-Tools.
 * Emcc exports this as _smoke_add.
 */
int smoke_add(int a, int b) {
    return a + b;
}
