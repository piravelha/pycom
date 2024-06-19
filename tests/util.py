import subprocess
from typing import Callable

def run_test(text: str, compile: Callable[[str, str], None]):
    compile("<tests>", text)
    with open("build/out.c") as f:
        got = f.read()
    subprocess.run([
        "gcc", "-o", "build/out.exe", "build/out.c"
    ])
    result = subprocess.run([
        "./build/out.exe",
    ], capture_output=True)
    return got, result.stdout.decode()