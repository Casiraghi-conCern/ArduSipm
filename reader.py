
#!/usr/bin/env python3

'''
 --------------------------------------------------------------------
|              aaa - ArduSiPM Acquisition & Analysis                 |
 --------------------------------------------------------------------
| Python libraries for the ArduSiPM                                  |
| project web: https://sites.google.com/view/particle-detectors/home |
| code repository: https://github.com/fmessi/aaa.git                 |
|                                                                    |
| history:                                                           |
| 191119 - F.Messi - import info script from V.Bocci original code   |
|                    load of data-file from F.Curti DAQ              |
| 200211 - F.Messi - Load data functions moved to a-load.py          |
|                    Data analysis functions moved to a-analysis.py  |
 --------------------------------------------------------------------
'''

import sys
import time
from datetime import datetime, timedelta
import serial
import serial.tools.list_ports
import IPython
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')

# import os
# import csv
# import numpy as np
# import pandas as pd

# import aaa_scripts
# import Utility as ut
# import a_load as lf
# import a_analysis as an

def menu_long(): 
    print('''
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

    ''')

def menu():
    print('''
    ===========================
        WELCOME TO ArduSiPM   
    ===========================
    type menu() for this menu
    
    available functions are:

    - Info_ASPM()
    - lf.Load_csv(filename=, debug=)
    - lf.LoadMerge_cvs(directory=, InName=, OutName=, debug=)

    - Plot_ADC(dati, binsize=16, hRange=[0,4000])

    - RunIt(duration_acq=0, file_par=)
    - RunLoop(duration_acq, nLoops, file_par)

    - menu_long()
    ===========================
    
    ''')

def interactive():
    print('''
    Interactive IPython shell 
    ===========================
    Quick command usage:
    - 'who' or 'whos' to see all (locally) defined variables
    - if the plots are shown only as black area, run '%gui qt'
    - to make cmd prompt usable while plots are shown use
      'plt.ion()' for interactive mode or run 
      'plt.show(block=False)' to show them
    ''')
    IPython.embed()


'''==================
     ArduSiPM interfacing
=================='''
def Info_ASPM():
    '''
    SCOPE: call to the original info script from V.Bocci
    INPUT: none
    OUTPUT: print info on screen
    '''
    sys.path.append('Valerio/')
    # import ArduSiPM_info.py

def Search_ASPM(baudrate=115200, timeout=None, debug=False):
    '''
    SCOPE: search for ArduSiPM
    NOTE: copied and adapted from the original script from V.Bocci
    INPUT: none
    OUTPUT: string with serial name
    '''
    #Scan Serial ports and found ArduSiPM
    if(debug): print('Serial ports available:')
    ports = list(serial.tools.list_ports.comports())
    for i in range(len(ports)):
        if(debug): print(ports[i])
        pippo=str(ports[i])
        if (pippo.find('Arduino')>0) or (pippo.find('cu.usbmodem')>0):
            serialport=pippo.split(" ")[0] #TODO: ? solve the com> com9 problem Francesco
            print(f"Found ArduSiPM in port {serialport}")
            return(str(serialport))
        else :
            print ("no ArduSiPM, looking more...")

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
            print('ArduSiPM not found please connect')
            return(0)
    return(ser)

def Scrivi_Seriale(comando, ser):
    if(ser):
        ser.write(str('m').encode('utf-8'))
        time.sleep(2)
        ser.write(str(comando).encode('utf-8'))
        time.sleep(2)
        ser.write(str('e').encode('utf-8'))
        print(f'wrote on serial {comando}')
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


'''==================
     Data acquisition
=================='''
def Save_Data(data, file_name='my_data.csv'):
    '''
    SCOPE:
    INPUT: file name and data in binary format
    OUTPUT:
    '''
    with open(file_name, 'w') as file:
        #writer = csv.writer(file, delimiter=',')
        for line in data:
            file.write(line)#.decode('ascii'))
            file.write(',')

def Acquire_ASPM(duration_acq, ser, debug=False):
    '''
    SCOPE:
    INPUT: duration in seconds
    OUTPUT: a DataFraMe with the data
    '''
    lista = []
    start_acq_time = datetime.now()
    stop_acq_time = start_acq_time + timedelta(seconds=duration_acq-1)
    acq_time = datetime.now()
    while(acq_time < stop_acq_time):
        acq_time = datetime.now()
        #print(acq_time.strftime('%H:%M:%S'))
        ser.reset_input_buffer() # Flush all the previous data in Serial port
        data = ser.readline().rstrip()
        tdata = f"u{acq_time.strftime('%y%m%d%H%M%S.%f')}{data.decode('ascii')}"
        if(debug): print(tdata)
        lista.append(tdata)
        time.sleep(0.2)
    return(lista)

def RunIt(duration_acq=0, file_par='RawData', threshold=200, debug=False):
    '''
    SCOPE:
    NOTE: copied and adapted from the original script from V.Bocci
    INPUT:
    OUTPUT:
    '''
    start_time = datetime.now()
    stopat = start_time+timedelta(seconds=duration_acq)
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
        print('ArduSiPM not found please connect')
        return(0)
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
    print(f'Acquiring now... this run will stop at {stopat}')
    data = Acquire_ASPM(duration_acq, ser, debug=debug)
    print('SAVING DATA...')
    Save_Data(data, f"{start_time.strftime('%y%m%d%H%M%S')}_{file_par}.csv")
    ser.close()
    return data

def RunLoop(duration_acq, nLoops, file_par, threshold=200):
    print(f'Start running {nLoops} loops of {duration_acq} sec each')
    print()
    for i in range(nLoops+1):
        print(f'Run now loop n. {i} of {nLoops}')
        RunIt(duration_acq=duration_acq, file_par=file_par, threshold=threshold)

def ScanThreshold(duration_acq=3600, debug=False, prefix=None):
    step = 20
    for t in range(10, 255, step):
        print(f'I will now run threshold {t} (range 10-255, steps {step})')
        time.sleep(10)
        nomeFile = prefix + f'CTA-ThresholdScan_{t}'
        RunIt(duration_acq=duration_acq, file_par=nomeFile, threshold=t, debug=debug)




'''==================
     Interactive menu
=================='''
menu()
interactive()
