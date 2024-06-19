#include <stdio.h>

int v0(int v1) {
    return (0 - v1);
}
int main() {
    printf("%d\n", v0(2));
    return 0;
}