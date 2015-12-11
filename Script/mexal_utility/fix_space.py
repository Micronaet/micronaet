#!/usr/bin/python
def only_ascii(value):
    ''' Return only ascii char
    '''
    value = value.strip()
    res = ""
    not_ascii = False
    for v in value:
        try:
            test = asc(v)
            res += v
        except:
            not_ascii = True
        
out = open("sodexo.out.csv", "w")
for l in open("sodexo.csv", "r"):
    l, not_ascii = only_ascii(l)
    out.write("%-30s;%5s;\r\n" % (l, not_ascii))
