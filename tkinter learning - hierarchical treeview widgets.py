from tkinter import *
from tkinter import ttk

treedata = Tk()
treedata.title("Tree data")

ttk.Label(treedata, text="Chess games").pack()
treeview = ttk.Treeview(treedata)
treeview.pack()

#Parent section
treeview.insert('', '0', 'item1', text="Please select your time format")

#Child section
treeview.insert('', '1', 'item2', text="Rapid")
treeview.insert('', '2', 'item3', text="Blitz")
treeview.insert('', 'end', 'item4', text="Bullet")

#Item 2's child section
treeview.insert('item2', 'end', '10 minutes', text="10:00 (10 minutes)")
treeview.insert('item2', 'end', '15 minutes, 10 second incremental', text="15|10 (15 minutes with 10 second incremental)")

#Item 3's child section
treeview.insert('item3', 'end', '5 minutes', text="5:00 (5 minutes)")
treeview.insert('item3', 'end', '3 minutes, 2 second incremental', text="3|2 (3 minutes with a 2 second incremental)")

#Item 4's child section
treeview.insert('item4', 'end', '2 minute, 1 second incremental', text="2|1 (2 minutes with a 1 second incremental)")
treeview.insert('item4', 'end', '1 minute', text="1:00 (1 minute)")

#placing the sections
treeview.move('item2', 'item1', 'end')
treeview.move('item3', 'item1', 'end')
treeview.move('item4', 'item1', 'end')

treedata.mainloop()