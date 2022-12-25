#!/usr/bin/env python3

from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import scrolledtext

import sys
import time
from datetime import datetime, timedelta
import serial
import serial.tools.list_ports
import IPython
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')
import os


#-------------------------------------------------------------
## GUI functions

def out_ins(text):
    global output
    output.config(state="normal")
    output.insert("end", f"\n   {text}")
    output.see(END)
    output.config(state="disabled")
def change_debug(event):
    global debug
    debug = not debug
def validate_mins_secs(value):
    if value.isdigit() and len(str(value)) != 4:
        value = int(value)
        if 0 <= value <= 60:
            return True
    return False
def validate_hours(value):
    if value.isdigit() and len(str(value)) != 4:
        value = int(value)
        if 0 <= value <= 999:
            return True
    return False
def sum_times():
    global tot_hours, tot_mins, tot_secs
    secs, mins, hours = tot_secs.get(), tot_mins.get(), tot_hours.get()
    tot = secs+60*mins+3600*hours
    return tot
def choose_path():
    global paths_cbox, save_path
    path = filedialog.askdirectory()
    save_path.set(path)

    tup = (path,)
    values = paths_cbox["values"]
    
    paths_cbox["values"] = values + tup

#-------------------------------------------------------------
## reader functions

def Info_ASPM():
    '''
    SCOPE: call to the original info script from V.Bocci
    INPUT: none
    OUTPUT: print info on screen
    '''
    sys.path.append('Valerio/')
def Search_ASPM(baudrate=115200, timeout=None):
    '''
    SCOPE: search for ArduSiPM
    NOTE: copied and adapted from the original script from V.Bocci
    INPUT: none
    OUTPUT: string with serial name
    '''
    global debug
    #Scan Serial ports and found ArduSiPM
    if(debug): out_ins("Serial ports available:") #print('Serial ports available:')
    ports = list(serial.tools.list_ports.comports())
    for i in range(len(ports)):
        if(debug): out_ins(ports[i]) #print(ports[i])
        pippo=str(ports[i])
        if (pippo.find('Arduino')>0) or (pippo.find('cu.usbmodem')>0):
            serialport=pippo.split(" ")[0] #TODO: ? solve the com> com9 problem Francesco
            #print(f"Found ArduSiPM in port {serialport}")
            out_ins(f"Found ArduSiPM in port {serialport}")
            return(str(serialport))
        else :
            #print("no ArduSiPM, looking more...")
            out_ins("no ArduSiPM, looking more...")
def Apri_Seriale():
    ser = serial.Serial()
    ser.baudrate = 115200
    ser.timeout=None
    ser_num = Search_ASPM()
    if (ser_num):
            ser.port = ser_num
            ser.open()
            time.sleep(1)
    else:
            #print('ArduSiPM not found please connect')
            out_ins("ArduSiPM not found please connect")
            return(0)
    return(ser)
def Scrivi_Seriale(comando, ser):
    if(ser):
        ser.write(str('m').encode('utf-8'))
        time.sleep(2)
        ser.write(str(comando).encode('utf-8'))
        time.sleep(2)
        ser.write(str('e').encode('utf-8'))
        #print(f'wrote on serial {comando}')
        out_ins(f'wrote on serial {comando}')
        time.sleep(0.5)
def SetThreshold(threshold, ser):
    if(ser):
        ser.write(str('m').encode('utf-8'))
        time.sleep(2)
        ser.write(str('t').encode('utf-8'))
        time.sleep(2)
        #ser.write(threshold.to_bytes(4, 'little'))
        #ser.write(b'10')
        ser.write(str(threshold).encode('utf-8'))
        time.sleep(4)
        ser.write(str('e').encode('utf-8'))
        time.sleep(2)
def Save_Data(data, file_name='my_data.csv'):
    '''
    SCOPE:
    INPUT: file name and data in binary format
    OUTPUT:
    '''
    global save_path
    with open(os.path.join(save_path.get(), file_name), 'w') as file:
        #writer = csv.writer(file, delimiter=',')
        for line in data:
            file.write(line)#.decode('ascii'))
            file.write(',')
def Acquire_ASPM(duration_acq, ser):
    '''
    SCOPE:
    INPUT: duration in seconds
    OUTPUT: a DataFraMe with the data
    '''
    global debug
    lista = []
    start_acq_time = datetime.now()
    stop_acq_time = start_acq_time + timedelta(seconds=duration_acq-1)
    acq_time = datetime.now()
    while(acq_time < stop_acq_time):
        acq_time = datetime.now()
        #print(acq_time.strftime('%H:%M:%S'))
        ser.reset_input_buffer() # Flush all the previous data in Serial port

        # data = ser.read_until(r'\n')
        # print(data)

        data = ser.readline().rstrip()
        tdata = f"u{acq_time.strftime('%y%m%d%H%M%S.%f')}{data.decode('ascii')}"
        if(debug): out_ins(tdata) #print(tdata)
        lista.append(tdata)
        time.sleep(0.2)
    return(lista)
def RunIt(duration_acq=0, file_par='RawData', threshold=200):
    '''
    SCOPE:
    NOTE: copied and adapted from the original script from V.Bocci
    INPUT:
    OUTPUT:
    '''
    global debug
    # start_time = datetime.now()
    # stopat = start_time+timedelta(seconds=duration_acq)
    ## serial connection
    ser = serial.Serial()
    ser.baudrate = 115200
    ser.timeout=None #try to solve delay
    ser_num = Search_ASPM()
    if (ser_num):
        ser.port = ser_num
        ser.open()
        time.sleep(1)
    else:
        #print('ArduSiPM not found please connect')
        out_ins("ArduSiPM not found please connect")
        return(0)    
    start_time = datetime.now()
    stopat = start_time+timedelta(seconds=duration_acq)
    ## acquisition
    #ser.write(b'a') # enable ADC
    #ser.write(b'd') # enable TDC
    #ser.write(b'h75') # set HV
    #Scrivi_Seriale(b's3', ser)
    #Scrivi_Seriale(b'@', ser)
    #time.sleep(0.5)
    #ser.write(b'@')
    #time.sleep(0.5)
    ser.write(b'#')
    time.sleep(0.5)
    SetThreshold(threshold, ser)
    ser.write(b'$')
    time.sleep(4)
    #ser.write(b'#') ## ADC+CPS
    ser.write(b'@') ## TDC+ADC+CPS
    time.sleep(0.5)
    #print(f'Acquiring now... this run will stop at {stopat}')
    out_ins(f'starting time: {start_time} \n    Acquiring now... this run will stop at {stopat}')
    data = Acquire_ASPM(duration_acq, ser)
    #print('SAVING DATA...')
    out_ins('SAVING DATA...')
    Save_Data(data, f"{start_time.strftime('%y%m%d%H%M%S')}_{file_par}.csv")
    ser.close()
    #print('Acquisition ended')
    out_ins('Acquisition ended\n')
    return data
def RunLoop(duration_acq, nLoops, file_par, threshold=200):
    #print(f'Start running {nLoops} loops of {duration_acq} sec each')
    #print()
    out_ins(f'Start running {nLoops} loops of {duration_acq} sec each\n')
    for i in range(nLoops+1):
        #print(f'Run now loop n. {i} of {nLoops}')
        out_ins(f'Run now loop n. {i} of {nLoops}')
        RunIt(duration_acq=duration_acq, file_par=file_par, threshold=threshold)
def ScanThreshold(duration_acq=3600, prefix=None):
    global debug
    step = 20
    for t in range(10, 255, step):
        #print(f'I will now run threshold {t} (range 10-255, steps {step})')
        out_ins(f'I will now run threshold {t} (range 10-255, steps {step})')
        time.sleep(10)
        nomeFile = prefix + f'CTA-ThresholdScan_{t}'
        RunIt(duration_acq=duration_acq, file_par=nomeFile, threshold=t, debug=debug)

# interactive()

#-------------------------------------------------------------------------------------
## useful variables

debug = False

initial_text = '''

    THIS IS ONLY A TEST PURPOSE TEXT. IT DOESN'T PROVIDE ANY USEFUL
    INSTRUCTION FOR THE CORRECT USAGE OF THIS VERSION.

    ===========================
        WELCOME TO ArduSiPM   
    ===========================
    type menu() for this menu

    available functions are:

    - Info_ASPM():             Retrive basic information from ArduSiPM 
    - Acquire_ASPM():          Open connection and start acquisition
    - Save_Data():             Save recorded data on a file
    
    - lf.Load_Curti_xlsx():    Load data from xlsx output file
    - lf.LoadMerge_xlsx():     Load all files from a folder (xlsx)
    - lf.Load_csv():           Load data from CVS output file
    - lf.LoadMerge_cvs():      Load all files from a folder (cvs)
    
    - Plot_ADC():              1D plot of ADC spectra
    
    - RunIt():               
    - RunLoop():
    - Acquire_ASPM()
    
    - menu_long()
    ===========================

    '''

y_time = 20
x_time = 100

backg_color = "#F0F0F0"
buttons_color = "#ECECEC"

current_dir = os.getcwd()
csv_files = os.path.join(current_dir, "csv_files")
icon_path = os.path.join(current_dir, "utilities", "icon.ico")

#-------------------------------------------------------------
## main window

root = Tk()
root.title("ArduSipm - Reader")
root.geometry("1100x600-100-100")
root.iconbitmap(icon_path)
root.resizable(False, False)

#-------------------------------------------------------------
## shown text

output_frame = Frame(root, bg="blue")

output = scrolledtext.ScrolledText(root, width=100, height=25)
out_ins(initial_text)

output.pack(fill=Y, expand=True)

#-------------------------------------------------------------
## top menu

menubar_1 = Menu(root)
root.config(menu=menubar_1)

file_menu = Menu(menubar_1, tearoff=0)
menubar_1.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Exit", command=root.quit)

#-------------------------------------------------------------
## canvas for acquisition

active_canvas = Canvas(root, bg=f"{backg_color}")

save_path = StringVar()
save_path.set(csv_files)

paths_cbox = ttk.Combobox(active_canvas, values=[csv_files], 
                          width=57, state="readonly", textvariable=save_path)
paths_button = Button(active_canvas, text="select path", command=choose_path,
                      bg=f"{buttons_color}")
path_label = Label(active_canvas, text="Destination of the CSV files:")

active_canvas.create_line(2, 2, 1100, 2, fill="grey")
active_canvas.create_rectangle(2, 4, 1097, 173, outline="grey")
# active_canvas.create_rectangle(x_time-51, y_time-2, 78, 41)

h_label = Label(active_canvas, text="hours")
m_label = Label(active_canvas, text="mins")
s_label = Label(active_canvas, text="secs")

tot_hours = IntVar()
tot_mins = IntVar()
tot_secs = IntVar()

acq_time_hours = Entry(active_canvas, justify="right", validate="key", textvariable=tot_hours, 
                       validatecommand=(root.register(validate_hours), "%P"))
acq_time_mins = Entry(active_canvas, justify="right", validate="key", textvariable=tot_mins, 
                      validatecommand=(root.register(validate_mins_secs), "%P"))
acq_time_seconds = Entry(active_canvas, justify="right", validate="key", textvariable=tot_secs,
                         validatecommand=(root.register(validate_mins_secs), "%P"))

run_button = Button(active_canvas, text="Run", command=lambda: RunIt(sum_times()),
                     bg=f"{buttons_color}")

debug_checkbox = Checkbutton(active_canvas, text="Debug")
debug_checkbox.bind("<Button-1>", change_debug)

#--------------------------------------------------------------
## packing everything

active_canvas.pack(side=BOTTOM, fill=BOTH, expand=True)
run_button.place(x=x_time-50, y=y_time - 1)
debug_checkbox.place(x=x_time+230, y=y_time-2)

acq_time_hours.place(x=x_time, y=y_time, width=25, height=20)
acq_time_mins.place(x=x_time+80, y=y_time, width=25, height=20)
acq_time_seconds.place(x=x_time+160, y=y_time, width=25, height=20)

h_label.place(x=x_time+30, y=y_time)
m_label.place(x=x_time+110, y=y_time)
s_label.place(x=x_time+190, y=y_time)

paths_cbox.place(x=x_time+510, y=y_time)
paths_button.place(x=x_time+880, y=y_time-3)
path_label.place(x=x_time+355, y=y_time)

#--------------------------------------------------------------

root.mainloop()