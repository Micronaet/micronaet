# -*- encoding: utf-8 -*-
# Modules used for ETL customers/suppliers note from Mexal
# use: ETL_note.py ANNOT.FIA

# Modules required:
import xmlrpclib, sys, ConfigParser, os
from datetime import date

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *   > Use the command with this syntax: python ./ETL_note.py ANNOT.FIA 
         *********************
         """
   sys.exit()

if sys.argv[1][-3:]=="FIA":
   cfg_file="openerp.cfg"
else: #"GPB"
   cfg_file="openerp.gpb.cfg"
   
# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read([cfg_file]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test
 
# For final user: Do not modify nothing below this line (Python Code) ********************************
# Functions:
def Prepare(valore):  
    #valore = unicode(valore, 'ISO-8859-1')
    # Windows-cp1252 ISO-8859-1
    valore=valore.decode('cp1252')
    valore=valore.encode('utf-8')
    valore=valore.replace("   ","")
    valore=valore.replace("\x00","")  
    valore=valore.replace("-------","-")  
    valore=valore.replace("*******","*")  
    return valore.strip()

def IsMexalCode(MexalCode, LenCode):
    try: 
       numeri="0123456789"
       lettere="abcdefghijklmnopqrstuvwxyz"  # TODO  Are all necessary?
       if len(MexalCode)<>LenCode: 
          return False
       else:
          #print "Testing: ", MexalCode  
          if (MexalCode[0] in numeri) and \
             (MexalCode[1] in numeri) and \
             (MexalCode[2] == ".") and \
             (MexalCode[3] in numeri) and \
             (MexalCode[4] in numeri) and \
             (MexalCode[5] in numeri) and \
             (MexalCode[6] in numeri) and \
             (MexalCode[7] in numeri) and \
             (MexalCode[8] == " ") and \
             (MexalCode[9].lower() in lettere) and \
             (MexalCode[10] in numeri) and \
             (MexalCode[11] in numeri) and \
             (MexalCode[12] in numeri):
             return True
          else:
             return False 
    except: 
       return False # in case of error test failed

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common')
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object')

# Open CSV passed file (see arguments) mode: read / binary, delimiation char ";"
FileInput=sys.argv[1]

f = open(FileInput, 'r')
TotalFile=Prepare(f.read())
Note={}

LenCode=13 # Format: "NN.NNNNN LNNN"
OldCode=""
Old_i=0
for i in range(0, len(TotalFile) - LenCode):
    if IsMexalCode(TotalFile[i : (i + LenCode)], LenCode): # Find a code format       
       if OldCode: # else is the first record, nothing to write
          if OldCode[:8] in Note.keys(): # TODO Test if is present          
             Note[OldCode[:8]] = Note[OldCode[:8]] + "\n" + OldCode[8:] + ") " + TotalFile[Old_i:i].strip() # add after
          else:
             Note[OldCode[:8]] = OldCode[8:] + ") " + TotalFile[Old_i:i].strip() 
          OldCode=TotalFile[i : (i + LenCode)] # Actual begin old          
       else:
          OldCode=TotalFile[i : (i + LenCode)]
          Old_i=i
       Old_i=i+LenCode # save actual i + len of code for get value 
       i+=LenCode # jump len code char

# print Note

for chiave in Note.keys():
    partner_id=sock.execute(dbname,uid,pwd,'res.partner','search',[('mexal_c','=',chiave[:8])])
    if partner_id:
       partner=sock.execute(dbname,uid,pwd,'res.partner','write',partner_id,{'mexal_note': '[Agg.: %s] %s' % (date.today().strftime('%Y-%m-%d'),Note[chiave])})
       print "[INFO] Note Update: ", chiave[:8], chiave, Note[chiave]
    #else:
       #print "[WARNING] Partner not found:",chiave[:8]

