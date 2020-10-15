import os

pip_reqs = os.path.join(os.path.split(os.path.realpath(__file__))[0], "pip_reqs.txt")
pip_listing = []

with open(pip_reqs, "r") as f:
    for line in f:
        line = line.strip().replace("-", "_")
        if "=" in line:
            new_line = ""
            for char in line:
                if char == "=":
                    break
                else:
                    new_line += char
            line = new_line.strip()
        if line:
            pip_listing.append(line)

errors = []

for p in pip_listing:
    try:
        __import__(p)
    except:
        errors.append(p)

exit(len(errors))
