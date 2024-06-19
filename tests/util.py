import subprocess
from typing import Callable

def run_test(text: str, compile: Callable[[str, str], None]):
    compile("<tests>", text)
    with open("out.c") as f:
        got = f.read()
    subprocess.run([
        "gcc", "-o", "out.exe", "out.c"
    ])
    result = subprocess.run([
        "./out.exe",
    ], capture_output=True)
    return got, result.stdout.decode()