#!/usr/bin/env python3

import os
import sys
import threading
import time
from datetime import datetime, timedelta
from tkinter import *
from tkinter import filedialog, scrolledtext, ttk

import serial
import serial.tools.list_ports

# -------------------------------------------------------------
# GUI functions

def out_ins(text):
    global output
    output.config(state="normal")
    output.insert("end", f"\n   {text}")
    output.see(END)
    output.config(state="disabled")

def validate_hours(value):
    if value == '':
        return True
    elif value.isdigit() and len(str(value)) <= 3:
        value = int(value)
        if 0 <= value < 1000:
            return True
    return False

def validate_mins(value):
    if value == '':
        return True
    elif value.isdigit() and len(str(value)) <= 2:
        value = int(value)
        if 0 <= value < 60:
            return True
    return False

def validate_secs(value):
    if value == '':
        return True
    elif value.isdigit() and len(str(value)) <= 2:
        value = int(value)
        if 0 <= value < 60:
            return True
    return False

acq_time_tot = 0

def sum_times():
    global tot_hours, tot_mins, tot_secs, acq_time_tot
    secs, mins, hours = tot_secs.get(), tot_mins.get(), tot_hours.get()
    secs = int(secs) if secs != '' else 0
    mins = int(mins) if mins != '' else 0
    hours = int(hours) if hours != '' else 0
    tot = secs+60*mins+3600*hours
    acq_time_tot = tot
    return tot

def choose_path():
    global save_path, shown_path
    path = filedialog.askdirectory(initialdir=save_path.get(), mustexist=True)
    if path != '':
        save_path.set(path)
        shown_path.set("Destination of the CSV files:           " + path)

def replace(widget, corner=False, which="both", positioning="prop"):
    global root_x, root_y
    w_x, w_y = widget.winfo_x(), widget.winfo_y()
    new_x, new_y = root.winfo_width(), root.winfo_height()
    x_ratio, y_ratio = new_x/root_x, new_y/root_y
    if w_x == 0 and w_y == 0 and not corner:
        return
    widget.place(x=w_x*x_ratio, y=w_y*y_ratio)

def replace_all():
    global replaceable_w, root_x, root_y
    for w in replaceable_w:
        replace(w)
    root_x, root_y = root.winfo_width(), root.winfo_height()

def check_config():
    global check_time
    if not (root_x == root.winfo_width() and root_y == root.winfo_height()):
        replace_all()
    root.after(check_time, check_config)

def launch_run():
    global can_run, stop_threads
    while not stop_threads:
        if can_run:
            RunIt(sum_times())
            can_run = False

def allow_run():
    global can_run
    if not run_thread.is_alive():
        run_thread.start()
    can_run = True

# -------------------------------------------------------------
# reader functions


def Info_ASPM():
    '''
    SCOPE: call to the original info script from V.Bocci
    INPUT: none
    OUTPUT: print info on screen
    '''
    sys.path.append('Valerio/')


def Search_ASPM():
    '''
    SCOPE: search for ArduSiPM
    NOTE: copied and adapted from the original script from V.Bocci
    INPUT: none
    OUTPUT: string with serial name
    '''
    global debug
    # Scan Serial ports and found ArduSiPM
    if (debug):
        out_ins("Serial ports available:")  # print('Serial ports available:')
    ports = list(serial.tools.list_ports.comports())
    for i in range(len(ports)):
        if (debug):
            out_ins(ports[i])  # print(ports[i])
        pippo = str(ports[i])
        if (pippo.find('Arduino') > 0) or (pippo.find('cu.usbmodem') > 0):
            # TODO: ? solve the com> com9 problem Francesco
            serialport = pippo.split(" ")[0]
            # print(f"Found ArduSiPM in port {serialport}")
            out_ins(f"Found ArduSiPM in port {serialport}")
            return (str(serialport))
        elif debug:
            out_ins("no ArduSiPM, looking more...")


def Apri_Seriale():
    ser = serial.Serial()
    ser.baudrate = 115200
    ser.timeout = None
    ser_num = Search_ASPM()
    if (ser_num):
        ser.port = ser_num
        ser.open()
        time.sleep(1)
    else:
        # print('ArduSiPM not found please connect')
        out_ins("ArduSiPM not found please connect")
        return (0)
    return (ser)


def Scrivi_Seriale(comando, ser):
    if (ser):
        ser.write(str('m').encode('utf-8'))
        time.sleep(2)
        ser.write(str(comando).encode('utf-8'))
        time.sleep(2)
        ser.write(str('e').encode('utf-8'))
        # print(f'wrote on serial {comando}')
        out_ins(f'wrote on serial {comando}')
        time.sleep(0.5)


def SetThreshold(threshold, ser):
    if (ser):
        ser.write(str('m').encode('utf-8'))
        time.sleep(2)
        ser.write(str('t').encode('utf-8'))
        time.sleep(2)
        # ser.write(threshold.to_bytes(4, 'little'))
        # ser.write(b'10')
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
        # writer = csv.writer(file, delimiter=',')
        for line in data:
            file.write(line)  # .decode('ascii'))
            file.write(',')


def Acquire_ASPM(duration_acq, ser):
    '''
    SCOPE:
    INPUT: duration in seconds
    OUTPUT: a DataFraMe with the data
    '''
    global debug, prog_bar
    prog_bar.stop()
    prog_bar.configure(mode="determinate")
    lista = []
    start_acq_time = datetime.now()
    stop_acq_time = start_acq_time + timedelta(seconds=duration_acq-1)
    acq_time = datetime.now()
    while (acq_time < stop_acq_time):
        prog_bar.step((10/(acq_time_tot*0.2)))
        acq_time = datetime.now()
        # print(acq_time.strftime('%H:%M:%S'))
        ser.reset_input_buffer()  # Flush all the previous data in Serial port

        # data = ser.read_until(r'\n')
        # print(data)

        data = ser.readline().rstrip()
        tdata = f"u{acq_time.strftime('%y%m%d%H%M%S.%f')}{data.decode('ascii')}"
        if (debug):
            out_ins(tdata)  # print(tdata)
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
    # serial connection
    ser = serial.Serial()
    ser.baudrate = 115200
    ser.timeout = None  # try to solve delay
    ser_num = Search_ASPM()
    if (ser_num):
        ser.port = ser_num
        ser.open()
        time.sleep(1)
    else:
        out_ins("ArduSiPM not found please connect")
        return(0)
    run_button.configure(state="disabled")
    paths_button.configure(state="disabled")
    acq_time_hours.configure(state="disabled")
    acq_time_minutes.configure(state="disabled")
    acq_time_seconds.configure(state="disabled")
    prog_bar.configure(mode="indeterminate")
    prog_bar.start()
    start_time = datetime.now()
    stopat = start_time+timedelta(seconds=duration_acq)
    # acquisition
    # ser.write(b'a') # enable ADC
    # ser.write(b'd') # enable TDC
    # ser.write(b'h75') # set HV
    # Scrivi_Seriale(b's3', ser)
    # Scrivi_Seriale(b'@', ser)
    # time.sleep(0.5)
    # ser.write(b'@')
    # time.sleep(0.5)
    ser.write(b'#')
    time.sleep(0.5)
    SetThreshold(threshold, ser)
    ser.write(b'$')
    time.sleep(4)
    # ser.write(b'#') ## ADC+CPS
    ser.write(b'@')  # TDC+ADC+CPS
    time.sleep(0.5)
    # print(f'Acquiring now... this run will stop at {stopat}')
    out_ins(
        f'starting time: {start_time} \n    Acquiring now... this run will stop at {stopat}')
    data = Acquire_ASPM(duration_acq, ser)
    # print('SAVING DATA...')
    out_ins('SAVING DATA...')
    Save_Data(data, f"{start_time.strftime('%y%m%d%H%M%S')}_{file_par}.csv")
    ser.close()
    # print('Acquisition ended')
    prog_bar.stop()
    out_ins('Acquisition ended\n')
    run_button.configure(state="normal")
    paths_button.configure(state="normal")
    acq_time_hours.configure(state="normal")
    acq_time_minutes.configure(state="normal")
    acq_time_seconds.configure(state="normal")
    return data


def RunLoop(duration_acq, nLoops, file_par, threshold=200):
    # print(f'Start running {nLoops} loops of {duration_acq} sec each')
    # print()
    out_ins(f'Start running {nLoops} loops of {duration_acq} sec each\n')
    for i in range(nLoops+1):
        # print(f'Run now loop n. {i} of {nLoops}')
        out_ins(f'Run now loop n. {i} of {nLoops}')
        RunIt(duration_acq=duration_acq, file_par=file_par, threshold=threshold)


def ScanThreshold(duration_acq=3600, prefix=None):
    global debug
    step = 20
    for t in range(10, 255, step):
        # print(f'I will now run threshold {t} (range 10-255, steps {step})')
        out_ins(f'I will now run threshold {t} (range 10-255, steps {step})')
        time.sleep(10)
        nomeFile = prefix + f'CTA-ThresholdScan_{t}'
        RunIt(duration_acq=duration_acq,
              file_par=nomeFile, threshold=t, debug=debug)

# interactive()

# -------------------------------------------------------------------------------------
# useful variables



debug = False
check_time = 100
stop_threads = False
can_run = True


initial_text = '''

    THIS IS ONLY A TEST PURPOSE TEXT. IT DOESN'T PROVIDE ANY USEFUL
    INSTRUCTION FOR THE CORRECT USAGE OF THIS VERSION.

    ===========================
        WELCOME TO ArduSiPM   
    ===========================
    

    '''

y_time = 500
x_time = 100

backg_color = "#F0F0F0"
buttons_color = "#ECECEC"

current_dir = os.getcwd()
csv_files = os.path.join(current_dir, "csv_files")
icon_path = os.path.join(current_dir, "utilities", "icon.ico")

if not os.path.exists(csv_files):
    os.mkdir("csv_files")

# -------------------------------------------------------------
# main window
root = Tk()

screen_x, screen_y = root.winfo_screenwidth(), root.winfo_screenheight()
root_x, root_y = int(screen_x*5/6), int(screen_y*5/6)
min_x = int(root_x*4/6)
min_y = int(min_x*root_y/root_x)

root.title("ArduSipm - Reader")
root.geometry(f"{root_x}x{root_y}-100-70")
try: root.iconbitmap(icon_path)
except TclError: pass
root.resizable(True, True)
root.minsize(width=min_x, height=min_y)
#root.after(check_time, check_config)

# -------------------------------------------------------------
# shown text
# output_frame = Frame(root, width=100, height=100)

output = scrolledtext.ScrolledText(root, height=25, highlightthickness=0)
out_ins(initial_text)

# -------------------------------------------------------------
# top menu

menubar_1 = Menu(root)
root.config(menu=menubar_1)

file_menu = Menu(menubar_1, tearoff=0)
menubar_1.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Exit", command=root.quit)

# -------------------------------------------------------------
# canvas for acquisition

save_path = StringVar()
save_path.set(csv_files)
shown_path = StringVar()
shown_path.set("Destination of the CSV files:           " + csv_files)

main_frame = Frame(root)
footer_frame = Frame(root)

# paths_cbox = ttk.Combobox(root, values=[csv_files],
#   width=56, state="readonly", textvariable=save_path, justify="right")
paths_button = Button(main_frame, text="select path", command=choose_path,
                      bg=f"{buttons_color}")
path_label = Label(footer_frame, textvariable=shown_path)

h_label = Label(main_frame, text="hours")
m_label = Label(main_frame, text="mins")
s_label = Label(main_frame, text="secs")

tot_hours = StringVar()
tot_mins = StringVar()
tot_secs = StringVar()

acq_time_hours = Spinbox(main_frame, justify="right", width=3, textvariable=tot_hours,
                         from_=0, to=999, validate="all", validatecommand=(root.register(validate_hours), "%P"))
acq_time_minutes = Spinbox(main_frame, justify="right", width=3, textvariable=tot_mins,
                           from_=0, to=59, validate="all", validatecommand=(root.register(validate_mins), "%P"))
acq_time_seconds = Spinbox(main_frame, justify="right", width=3, textvariable=tot_secs,
                           from_=0, to=59, validate="all", validatecommand=(root.register(validate_secs), "%P"))

footer_frame.pack(side="bottom", fill="x")

run_thread = threading.Thread(target=launch_run, name="Run", daemon=True)
run_button = Button(main_frame, text="Run", bg=f"{buttons_color}",
                command=allow_run)

prog_frame = Frame(root)
prog_bar = ttk.Progressbar(prog_frame, maximum=100,
                           length=500)

# prog_label = Label(prog_frame, textvariable=prog)
prog_frame.pack()
prog_bar.pack()
# prog_label.pack()

# --------------------------------------------------------------
# packing everything

output.pack(side="top", fill="x")

main_frame.pack(pady=15)

acq_time_hours.pack(side="left")
h_label.pack(side="left")

acq_time_minutes.pack(side="left")
m_label.pack(side="left")

acq_time_seconds.pack(side="left")
s_label.pack(side="left")

run_button.pack(side="left", padx=10)

paths_button.pack(side="left")
path_label.pack(side='bottom', anchor="se", padx=10)

# --------------------------------------------------------------
replaceable_w = []
replaceable_w_x = []
replaceable_w_y = []
root.mainloop()

stop_threads = True