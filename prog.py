from tkinter import *
from tkinter import ttk
import time

root = Tk()

prog_bar = ttk.Progressbar(root, maximum=100,
            length=500, mode="determinate")
prog_bar.pack()

prog_bar.start()

root.mainloop()