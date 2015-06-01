#!/usr/bin/python
from Tkinter import *
import tkMessageBox
import sys
import os

root = Tk()
mexal_command = r"c:\mexal_cli\prog\mxdesk00.exe -x2 -t0 -a%s -p#%s -k%s:%s"

#-------
# Event:
#-------

#def keypress(event):
#    print "Pressed:", repr(event.char)
    
#def mouse_left_click(event):
#    frame.focus_set()
#    print "Left Clicked at", event.x, event.y

#def mouse_right_click(event):
#    frame.focus_set()
#    print "Right Clicked at", event.x, event.y

#def quit():
#    if tkMessageBox.askokcancel("Quit", "Do you really wish to quit?"):
#        root.destroy()

def exit_click():
    root.destroy()
    
def mexal_click():
    try:
        os.system("gedit")
        root.destroy()
        #os.system(mexal_command % (
        #    'tet',     # company
        #    '361',     # sprix
        #    'lucrin',  # user
        #    'lu999ri', # password
        #))
        #root.destroy()
        
    except:
        tkMessageBox.showerror("Error launching Mexal", sys.exc_info())
    
#root.protocol("WM_DELETE_WINDOW", quit)
def smart_entry(parent, caption, width=None, **options):
    Label(parent, text=caption).pack(side=LEFT)
    entry = Entry(parent, **options)
    if width:
        entry.config(width=width)
    entry.pack(side=LEFT)
    return entry
    
# Draw windows:
frame = Frame(root, width=300, height=200)
#frame.bind("<Button-1>", mouse_left_click)
#frame.bind("<Button-3>", mouse_right_click)
#frame.bind("<Key>", keypress)
frame.pack_propagate(0) # don't shrink
frame.pack()

# Edit box:
#password = Entry(root)
#password.pack()
#password.focus_set()

#user = makeentry(parent, "User name:", 10)
password = smart_entry(root, "Password:", 10, show="*")
company = smart_entry(root, "Company:", 10)


# Button
mexal = Button(frame, text="Mexal", command=mexal_click)
mexal.pack()

exit = Button(frame, text="Exit", command=exit_click)
exit.pack()

root.mainloop()
