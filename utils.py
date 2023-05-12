
def bytes_to_str(x):
    s = ""
    for i, val in enumerate(x):
        if i%8==0:
            print(s)
            s = ""
        s +='0x{:02x} '.format(val)
        if i == len(x) -1 :
            print(s)
