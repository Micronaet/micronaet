#!/usr/bin/python
# -*- encoding: utf-8 -*-

import os
from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

# Parameters: #################################################################
# Transit files:
path = "c:\mexal_cli\prog"
file_cl = r"%s\production\%s"%(path, "esito_cl.txt")
file_cl_upd = r"%s\production\%s"%(path, "esito_cl_upd.txt")
file_sl = r"%s\production\%s"%(path, "esito_sl.txt")

# Sprix:
company_code = "PAN"
admin = "admin"
password = "password"

# Sprix list:
sprix_cl = 125
sprix_cl_upd = 126
sprix_sl = 127
sprix_bom = 608

# XMLRPC server:
xmlrpc_host = "10.0.0.222"
xmlrpx_port = 8000

sprix_command = r"%s\mxdesk.exe -command=mxrs.exe -login=openerp -t0 -x2 win32g -p#%s -a%s -k%s:%s"%(path, "%s",company_code, admin, password)

# result file are the same with "esito_" before file name

# Restrict to a particular path. ##############################################
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

# Create server: ##############################################################
server = SimpleXMLRPCServer((xmlrpc_host, xmlrpx_port), requestHandler=RequestHandler)
server.register_introspection_functions()

# Functions: ##################################################################
def sprix(operation):
    ''' Call pxrs program passing sprix number
    '''
    def get_res(transit_file, is_list=False):
        """ Read result files, composed ad transit_file with "esito_" before
            return value of the only one line that is present
        """
        try:
            res_file = open(transit_file, "r")
            
            if is_list:
                res=[]
                for item in res_file:
                    code=item[:6].strip()
                    operation= "OK" == item[6:8].upper()
                    res.append((code, operation))
            else:        
                res = res_file.read().strip()

            res_file.close()
            os.remove(transit_file)    
            return res                
        except:
            return False # for all errors    
        
    if operation.upper() == "CL": # call sprix for create CL: #################
        try:
            os.system(sprix_command%(sprix_cl))            
        except:
            return "#Error launching importation CL command" # on error    
        
        # get result of operation:
        return get_res(file_cl) 
        
    elif operation.upper() == "CLW": # call sprix for update price in CL: #####
        try:
            os.system (sprix_command%(sprix_cl_upd))
        except:
            return False # on error    
        
        # get result of operation:
        return get_res(file_cl_upd, is_list=True)
        
    elif operation.upper() == "SL": # call sprix for create SL: ###############
        try:
            os.system (sprix_command%(sprix_sl))
        except:
            return "#Error launching importation SL command" # on error    
        
        # get result of operation:
        return get_res(file_sl) 

    elif operation.upper() == "BOM": # call sprix for create BOM: #############
        try:
            os.system (sprix_command%(sprix_bom))
        except:
            return "#Error launching export BOM" 
        
        # get result of operation:
        return get_res(file_sl) 

    return False # error

# Register Function in XML-RPC server: ########################################
server.register_function(sprix, 'sprix')

# Run the server's main loop ##################################################
server.serve_forever()

