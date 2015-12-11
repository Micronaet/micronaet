#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime, timedelta
from os import listdir
from os.path import isfile, join
import ConfigParser

# -----------
# Parameters:
# -----------
cfg_file = "openerp.cfg" # same directory
config = ConfigParser.ConfigParser()
config.read(cfg_file)

# SMTP paramenter for log mail:
smtp_server = config.get('smtp', 'server')
smtp_user = config.get('smtp', 'user')
smtp_password = config.get('smtp', 'password')
smtp_port = int(config.get('smtp', 'port'))
smtp_SSL = eval(config.get('smtp', 'SSL'))
from_addr = config.get('smtp', 'from_addr')
to_addr = config.get('smtp', 'to_addr')
smtp_subject_mask = config.get('smtp', 'subject_mask')

# Mexal parameters:
mexal_company = config.get('mexal', 'company')
mexal_user = config.get('mexal', 'user')
mexal_password = config.get('mexal', 'password')

# Setup depend on parameter passed (default SDX if not present)
try:
    company = sys.argv[1]
except:
    company = "SDX" # default company

try:
    # Read parameters depend on start up company:
    file_err = config.get(company, 'file_err')          # Log file from mexal (empty = OK, else error)
    path_in = config.get(company, 'path_in')            # Folder: in files
    path_out = config.get(company, 'path_out')          # Folder: destination
    path_history = config.get(company, 'path_history')  # Folder: history
    log_file_name = config.get(company, 'log_file_name')
    sprix_number = int(config.get(company, 'sprix_number'))
    # Jump order too new:
    jump_order_days = eval(config.get(company, 'jump_order_days'))
    left_start_date = int(config.get(company, 'left_start_date'))
    left_days = int(config.get(company, 'left_days'))
except:
    print "[ERR] Chiamata a ditta non presente (scelte possibili: SDX o ELI)"
    sys.exit() # wrong company!

log_file = open(log_file_name, 'a')

# -----------------
# Utility function:
# -----------------
def log_message(log_file, message, model='info'):
    ''' Write log file and print log file
        log_file: handles of file
        message: text of message
        model: type of message, like: 'info', 'warning', 'error'
    '''
    log_file.write("[%s] %s: %s\n" % (
        model.upper(),
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        message, ))
    print message
    return

def get_smtp(log_message):
    # Start session with SMTP server
    try:
        from smtplib import SMTP
        smtp = SMTP()
        smtp.set_debuglevel(0)
        smtp.connect(smtp_server, smtp_port)
        smtp.login(smtp_user, smtp_password)
        log_message(
            log_file, 
            "Connesso al server %s:%s User: %s Pwd: %s" % (
                smtp_server, smtp_port, smtp_user, smtp_password))
        return smtp
    except:        
        log_message(
            log_file, 
            "Impossibile collegarsi server %s:%s User: %s Pwd: %s" % (
                smtp_server, smtp_port, smtp_user, smtp_password),
            'error', )
        return False
    
# -----------------------------------------------------------------------------
#                    Program: (NO CHANGE OVER THIS LINE)
# -----------------------------------------------------------------------------
# Mexal parameters:
sprix_command = r"c:\mexal_cli\prog\mxdesk.exe -command=mxrs.exe -a%s -t0 -x2 win32g -p#%s -k%s:%s" % (
    mexal_company, sprix_number, mexal_user, mexal_password)

if datetime.today().weekday() > 2: # TODO (change depend on number of day left)
        left_days += 2
        log_message(log_file, "Aggiunto due giorni extra alla data")

max_date = (datetime.today() + timedelta(days=left_days)).strftime("%Y%m%d")
log_message(log_file, "Valutazione scadenza, salto se >= %s)" % max_date)

# Get list of files and sort before import
file_list = []

try:
    # Sort correctly the files:       
    for file_in in [f for f in listdir(path_in) if isfile(join(path_in, f))]:
        file_list.append(
            (os.path.getctime(join(path_in, file_in)), file_in))
    file_list.sort()

    # Print list of sorted files for loggin the operation:
    for ts, file_in in file_list:
        log_message(log_file, "ID: Date: %s\t File: %s" % (
            datetime.fromtimestamp(ts), file_in ))
except:
    log_message(
        log_file, 
        "Impossibile leggere i file da elaborare, script terminato",
        'error', )
    sys.exit()    
       
# Import files sorted
order_imported = ""
for ts, file_in in file_list:
    import pdb; pdb.set_trace()
    # Jump file to delivery in 'left_days' days (usually 3):
    if jump_order_days:
        fin = open(join(path_in, file_in), "r")
        test_date = fin.readline()[left_start_date:left_start_date + 8]
        fin.close()
        if test_date >= max_date:
            log_message(log_file,
                "File saltato limite %s < data file %s" % (
                    max_date, test_date), "warning")
            continue
    log_message(log_file, "Divisione file: %s > %s" % (path_in, file_in))
    mail_error = "" # reset for every file readed
   
    # Output file parameters (open every loop because closed after import):
    file_out = {
        open(join(path_out, 'ordine.1.txt'), "w"): [0, 2036],
        open(join(path_out, 'ordine.2.txt'), "w"): [2036, 3507], # 1561
        }

    # Remove log file (if present):
    try:
        os.remove(file_err)
    except:
        pass

    # Split input file:
    fin = open(join(path_in, file_in), "r")
    for line in fin:
        position = 0
        for f in file_out:
            f.write("%s\r\n" % (line[
                file_out[f][0] : file_out[f][1]]))

    # Close all file (input and 2 splitted)       
    for f in file_out:
        try:
            f.close()
        except:
            mail_error += "Errore chiudendo file split\n"
    try:       
        fin.close()
    except:
        mail_error += "Errore chiudendo il file di input\n"
   
    # Run mexal:
    os.system(sprix_command)
   
    # Read error file for returned error:
    try:
        f_err = open(file_err, "r")
        test_err = f_err.read().strip() # ok if work
        if test_err[:2] != "ok":
            mail_error += test_err or "Errore generico (non gestito)"
        else:
            result = test_err.split(";")
            order_imported += "\tCliente %s - Interno: %s (Scad.: %s\n" % (
                result[1], result[2], test_date)
            log_message(log_file, " Ordine importato: %s" % (result, ))
        f_err.close()
    except:
        mail_error += "Errore generico di importazione (file log non trovato)!"
        pass # No file = no error
       
    if mail_error: # Comunicate
        log_message(
            log_file, "Errore leggendo il file: %s" % mail_error, 'error')

        # Send mail for error (every file):
        smtp = get_stmp(log_message)
        if smtp:    
            smtp.sendmail(
                from_addr, to_addr,
                "From: %s\nTo: %s\nSubject: %s\nDate: %s\n\n%s" % (
                    from_addr, to_addr, smtp_subject_mask % file_in,
                    datetime.now().strftime("%d/%m/%Y %H:%M"), mail_error))
            smtp.quit()       
            log_message(log_file, "Invio mail errore importazione: da %s, a %s, \n\t<<<%s\t>>>" % (
                from_addr, to_addr, mail_error))    
        else:
            log_message(
                log_file, 
                "Mail errore importazione non iviata %s, a %s, \n\t<<<%s\t>>>" % (
                    from_addr, to_addr, mail_error), 'error')   
                    
    else:
        # History the file (only if no error)
        try:
            os.rename(join(path_in, file_in), join(path_history, file_in))
            log_message(
                log_file, "Importato il file e storicizzato: %s" % file_in)
        except:
            log_message(
                log_file, "Errore storicizzando il file: %s" % file_in,
                'error')
            
if order_imported: # Comunicate importation   
    smtp = get_smtp(log_message)
    if smtp:
        smtp.sendmail(
            from_addr, to_addr,
            "From: %s\nTo: %s\nSubject: %s\nDate: %s\n\n%s" % (
                from_addr, to_addr, 'Ordini importati',
                datetime.now().strftime("%d/%m/%Y %H:%M"),
                order_imported))
        smtp.quit()
        log_message(log_file, "Mail ordini importati: da %s, a %s, \n\t<<<%s\t>>>" % (
            from_addr, to_addr, order_imported))
    else:
        log_message(
            log_file, 
            "Mail ordini importati non inviata: da %s, a %s, \n\t<<<%s\t>>>" % (
                from_addr, to_addr, order_imported), "error")
            
# Close operations:
try:
    log_file.close()    
except:
    pass
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

