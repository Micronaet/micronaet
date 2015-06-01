import pdb

path_root="/home/administrator/ETL/ambulatorio/"
path_mach2="/home/administrator/ETL/ambulatorio/MACH2/"

f = open('./db_list.txt', 'r')
f_commands = open('./dbf2txt.sh', 'w')

#pdb.set_trace()
for line in f:
    print line,
    file_db=line[len(path_mach2):-1]
    file_txt=file_db[:-4] + ".TXT"
    #import pdb; pdb.set_trace()
    f_commands.write("dbview %s%s > %sDB/%s\n"%(path_mach2, file_db, path_root, file_txt))
f.close()
f_commands.close()
