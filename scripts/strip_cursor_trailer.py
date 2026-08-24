import sys

text = sys.stdin.read()
lines = [line for line in text.splitlines() if "Co-authored-by: Cursor" not in line]
while lines and not lines[-1].strip():
    lines.pop()
sys.stdout.write("\n".join(lines) + ("\n" if lines else ""))
