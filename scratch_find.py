import os

root_dir = r"c:\Users\shrin\OneDrive\Desktop\CalmSphere"

for r, ds, fs in os.walk(root_dir):
    if ".venv" in r or "__pycache__" in r or ".git" in r:
        continue
    for f in fs:
        path = os.path.join(r, f)
        print(path)
