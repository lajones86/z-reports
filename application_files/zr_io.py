def enter_text(text):
    print(text)
    input("Press Enter key.")
    return(0)

def nostop(text):
    enter_text(text)
    return(0)

def message(text):
    enter_text(text)
    exit(0)

def error(text):
    enter_text(text)
    exit(9001)

def fatal(text):
    error(text)

#return true if yes, false if no
def yes_no(prompt):
    opt = "x"
    while opt == "x":
        print("\n%s" % prompt)
        opt = input("[y/n]: ")
        if opt.lower().strip() == "y":
            return(True)
        elif opt.lower().strip() == "n":
            return(False)
        else:
            opt = "x"
