import os
import sys

app_files = os.path.join(os.path.dirname(os.path.realpath(__file__)), r"..\application_files")

if len(sys.argv) < 2:
    print("Requires string(s) as argument(s).")
    exit(0)

for i in os.listdir(app_files):
    printed_name = False
    if os.path.splitext(i)[1].lower() == ".py":
        with open(os.path.join(app_files, i), "r") as f:
            for line in f:
                line_match = True
                for arg in sys.argv[1::]:
                    if not arg in line:
                        line_match = False
                        break
                if line_match == True:
                    if printed_name == False:
                        print(os.path.join(app_files, i))
                        printed_name = True
                    print(line)
exit(0)
