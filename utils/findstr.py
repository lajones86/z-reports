import os
import sys

app_files = os.path.join(os.path.dirname(os.path.realpath(__file__)), r"..\application_files")

if len(sys.argv) != 2:
    print("Requires string as argument.")
    exit(0)

for i in os.listdir(app_files):
    if os.path.splitext(i)[1].lower() == ".py":
        with open(os.path.join(app_files, i), "r") as f:
            for line in f:
                if sys.argv[1] in line:
                    print(i)
                    break

exit(0)
