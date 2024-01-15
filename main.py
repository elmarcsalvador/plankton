import serial
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import time
import platform
from math import log
from tktooltip import ToolTip
from discord_webhook import DiscordWebhook, DiscordEmbed
import webbrowser

# Global variables
reading_active = False
last_data = ''
received_data = ""
dbug = None
about_window = None
feedback_window = None
moist_calib_data = 1023
moist_max = 1023
count = 1
start_time = "Nil"

#For error handling
photo_hold=''
moist_hold=''
temp_fault=''
npk_hold=''

# Create the Tkinter window
window = tk.Tk()
window.title("PLANKTON > CONTROL PANEL")
window.geometry('720x380+50+50')
window.resizable(False,False)
menubar = tk.Menu(window)
window.config(menu=menubar)

# Function to set the theme based on the OS
def set_theme():
    if platform.system() == "Windows":
        window.tk_setPalette(background='#F0F0F0', foreground='#000000', activeBackground='#4CAF50', activeForeground='#FFFFFF')
        ttk.Style().theme_use('vista')
    elif platform.system() == "Darwin":  # macOS
        window.tk_setPalette(background='#E0E0E0', foreground='#000000', activeBackground='#4CAF50', activeForeground='#FFFFFF')
        ttk.Style().theme_use('aqua')
    else:  # Linux or other
        window.tk_setPalette(background='#E0E0E0', foreground='#000000', activeBackground='#4CAF50', activeForeground='#FFFFFF')
        ttk.Style().theme_use('clam')

# Set the theme based on the OS
set_theme()

# Set the main banner
banner = tk.Label(window, text="PLANKTON CONTROL PANEL")
banner.place(x=270,y=10)

# Set the plant name
name_label = tk.Label(window, text="Plant Name: ")
name_label.place(x=575,y=100)
name=tk.StringVar()
name_entry = ttk.Entry(window, textvariable=name)
name_entry.place(x=550,y=120)
ToolTip(name_entry, "Enter name of the plant under observation")
name.set("Unknown")

# Create labels to display individual values
sensor_stat = tk.Label(window, text="Sensors", fg="black")
sensor_stat.place(x=580,y=230)

sensor1_stat = tk.Label(window, text="Photo Sensor: ")
sensor1_stat.place(x=540,y=260)

sensor2_stat = tk.Label(window, text="Moist. Sensor: ")
sensor2_stat.place(x=540,y=280)

sensor3_stat = tk.Label(window, text="Temp. Sensor: ")
sensor3_stat.place(x=540,y=300)

sensor4_stat = tk.Label(window, text="NPK Sensor: ")
sensor4_stat.place(x=540,y=320)

sensor1 = tk.Label(window, text="---", fg="blue")
sensor1.place(x=640,y=260)

sensor2 = tk.Label(window, text="---", fg="blue")
sensor2.place(x=640,y=280)

sensor3 = tk.Label(window, text="---", fg="blue")
sensor3.place(x=640,y=300)

sensor4 = tk.Label(window, text="---", fg="blue")
sensor4.place(x=640,y=320)

label0_stat = tk.Label(window, text="Status: ", fg="black")
label0_stat.place(x=280,y=100)

label0 = tk.Label(window, text="Reading Stopped!", fg="red")
label0.place(x=320,y=100)

label1 = tk.Label(window, text="Light Intensity: NIL")
label1.place(x=55,y=170)

label2 = tk.Label(window, text="Soil Moisture: NIL")
label2.place(x=55,y=200)

label3 = tk.Label(window, text="Temperature: NIL")
label3.place(x=55,y=230)

label4 = tk.Label(window, text="Nitrogen: NIL")
label4.place(x=55,y=260)

label5 = tk.Label(window, text="Phosphorus: NIL")
label5.place(x=55,y=290)

label6 = tk.Label(window, text="Potassium: NIL")
label6.place(x=55,y=320)


def on_com_port_selected(port):
    selected_com_port.set(port)

def update_com_ports_menu(*args):
    # Clear existing menu entries
    com_ports_menu.delete(0, tk.END)

    # Add new menu entries with a black dot next to the selected port
    for index, port in enumerate(com_ports):
        label_text = f"{port} \u2022" if port == selected_com_port.get() else port
        com_ports_menu.add_command(label=label_text, command=lambda p=port: on_com_port_selected(p))



# Create a COM port selector
com_port_label = tk.Label(window, text="Select COM Port:")
com_port_label.place(x=565,y=160)

com_ports = [f"COM{i+1}" for i in range(10)]  # Adjust the range based on your needs
selected_com_port = tk.StringVar()
com_port_combobox = ttk.Combobox(window, textvariable=selected_com_port, values=com_ports)
com_port_combobox.set(com_ports[0])  # Set the default COM port
com_port_combobox.place(x=540,y=180)
com_port_combobox.bind('<<ComboboxSelected>>', lambda event: on_com_port_selected(com_port_combobox.get()))
ToolTip(com_port_combobox, "Select COM port to which the device is connected")
selected_com_port.set("COM1")
# Trace changes in the StringVar
selected_com_port.trace_add('write', update_com_ports_menu)
com_ports_submenu_label = tk.StringVar()
com_ports_submenu_label.set(f"Select COM Port: {selected_com_port.get()}")

# Create labels to display the system time and date
time_label = tk.Label(window, text="Time: ")
time_label.place(x=65,y=100)

date_label = tk.Label(window, text="Date: ")
date_label.place(x=20,y=120)

#def map_range(x, in_min, in_max, out_min, out_max):
#    return(x - in_min)*(out_max-out_min) // (in_max - in_min) + out_min

def error_code(x):
    if x == '0':
        return ("Operational","green")
    if x == '1':
        return ("Inoperational","red")
    if x == '2':
        return("Standby","indigo")

def moist_range(x, out_max):
    return (x)*(out_max)//(1023)

def light_range(x):
    return (x)*(100)//(1023)

def temp_cel(x):
    int(x)
    if x == 0:
        temperature = -83.63
        return temperature
    else:
        output_voltage = ( (x * 5.0) / 1023.0 )
        thermistor_resistance = ( ( 5 * ( 10.0 / output_voltage ) ) - 10 )
        thermistor_resistance = thermistor_resistance * 1000 
        therm_res_ln = log(thermistor_resistance)
        temperature = ( 1 / ( 0.001129148 + ( 0.000234125 * therm_res_ln ) + ( 0.0000000876741 * therm_res_ln * therm_res_ln * therm_res_ln ) ) )
        temperature = temperature - 273.15
        temperature = ("%.2f" % temperature)
        return temperature

# Function to read and display serial data
def read_serial():
    global reading_active
    global received_data
    global count
    global start_time
    reading_active = True
    start_time = time.strftime("%H%M%S_%d%m%Y")
    label0.config(text="Reading started!", fg='green')
    selected_port = selected_com_port.get()

    try:
        ser = serial.Serial(selected_port, 9600, timeout=1)
    except serial.SerialException:
        messagebox.showerror("Error", "Failed to establish a serial connection.")
        label0.config(text="Reading Stopped!", fg='red')
        return

    # Disable the "Start Reading" button
    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)

    while reading_active:
        data = ser.readline().decode('utf-8').strip()

        if data:
            #print(data)
            global photo_hold
            global moist_hold
            global temp_fault
            global npk_hold
            global last_data
            values = data.split(',')
            photo_hold = str(int(values[0]))
            moist_hold = str(int(values[1]))
            temp_fault = str(int(values[2]))
            npk_hold = str(int(values[3]))
            light = str(light_range(int(values[4])))
            moist = str(moist_range(int(values[5]),moist_max))
            temp = str(temp_cel(int(values[6])))
            nitro = values[7]
            phos = values[8]
            pota = values[9]
            last_data=(f'{light},{moist},{temp},{nitro},{phos},{pota}'+'\n')
            prog_data=(f'{light},{moist},{temp},{nitro},{phos},{pota}')
            received_data += prog_data + '\n'
            #print(last_data)
            print("ping!")
            label0.config(text=f"Processing data! ({count})", fg='green')
            process_data(data)
            count+=1

        window.update()

# Function to process and display individual values
def process_data(data):
    global disp_fault
    global photo_hold
    global moist_hold
    global temp_fault
    global npk_hold
    values = data.split(',')
    if len(values) == 10:
        
        sen1 = error_code(photo_hold)
        sensor1.config(text=sen1[0], fg=sen1[1])
        sen2 = error_code(moist_hold)
        sensor2.config(text=sen2[0], fg=sen2[1])
        sen3 = error_code(temp_fault)
        sensor3.config(text=sen3[0], fg=sen3[1])
        sen4 = error_code(npk_hold)
        sensor4.config(text=sen4[0], fg=sen4[1])
        
        label1.config(text="Light Intensity: " + str(light_range(int(values[4]))) + " %")
        label2.config(text="Soil Moisture: " + str(moist_range(int(values[5]),moist_max)) + " %")
        label3.config(text="Temperature: " + str(temp_cel(int(values[6]))) + " C")
        label4.config(text="Nitrogen: " + values[7] + " mg/kg")
        label5.config(text="Phosphorus: " + values[8] + " mg/kg")
        label6.config(text="Potassium: " + values[9] + " mg/kg")
        global moist_calib_data
        moist_calib_data = int(values[5])

# Function to stop reading serial data
def stop_reading():
    global reading_active
    reading_active = False
    sensor1.config(text="---", fg='blue')
    sensor2.config(text="---", fg='blue')
    sensor3.config(text="---", fg='blue')
    sensor4.config(text="---", fg='blue')
    label0.config(text="Reading Stopped!", fg='red')
    label1.config(text="Light Intensity: NIL")
    label2.config(text="Soil Moisture: NIL")
    label3.config(text="Temperature: NIL")
    label4.config(text="Nitrogen: NIL")
    label5.config(text="Phosphorus: NIL")
    label6.config(text="Potassium: NIL")
    # Enable the "Start Reading" button
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)

# Function to save accumulated data to a file
def save_to_file():
    global received_data
    global start_time
    stop_reading()
    plant_name = name.get()
    plant_name = plant_name.replace(" ", "_")
    current_time = time.strftime("%H%M%S_%d%m%Y")
    file_name = f"{plant_name}-{start_time}-{current_time}.txt"
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")], initialfile=file_name)

    if file_path:
        with open(file_path, 'w') as file:
            file.write(received_data)


# Function to update the system time and date label
def update_time_label():
    current_time = time.strftime("%H:%M:%S")
    time_label.config(text="Time: " + current_time)

    current_date = time.strftime("%A, %d %B %Y")
    date_label.config(text="Date: " + current_date)

    # Schedule the next update after 1000 milliseconds (1 second)
    window.after(1000, update_time_label)
    
# Initialize the system time and date labels
update_time_label()

def calibrate_moisture():
    # Show a custom warning dialog box
    result = messagebox.askquestion("Calibrate Moisture", "Are you sure to calibrate moisture sensor?\nWARNING! THIS WILL DELETE ALL PREVIOUS SESSSION DATA")
    
    if result == 'yes':
        #print("Calibrating moisture...")
        global moist_calib_data
        global moist_max
        global received_data
        global count
        global current_val
        stop_reading()
        moist_max=moist_calib_data
        current_val.config(text=f"Current Max: {moist_max}")
        received_data = ""
        count = 0
        messagebox.showinfo("Calibration Success",f"Moisture Calibration Done!\nMax Moist ADC value set to {moist_max}")

def debug():
    #print("debug")
    global dbug
    if dbug is None or not dbug.winfo_exists():
        dbug = tk.Toplevel(window)
        dbug.title("PLANKTON > DEBUG")
        dbug.geometry('320x144+50+50')
        dbug.resizable(False,False)
        global debug_text
        global current_val
        rawadc_label = tk.Label(dbug,text="RAW Serial Data")
        rawadc_label.place(x=0,y=0)
        debug_text = scrolledtext.ScrolledText(dbug, wrap=tk.WORD, width=25, height=7)
        debug_text.config(state=tk.DISABLED)
        debug_text.place(x=0, y=20)
        calibrate_button = ttk.Button(dbug, text="Calibrate Moist", command=calibrate_moisture)
        calibrate_button.place(x=220,y=80)
        ToolTip(calibrate_button, "Calibrate current moisture value as max")
        current_val = tk.Label(dbug, text=f"Current Max: {moist_max}")
        current_val.place(x=215,y=30)
        update_debug_text()
    else:
        dbug.lift()

def update_debug_text():
    global reading_active
    
    if reading_active == True:
        debug_text.config(state=tk.NORMAL)
        # Insert the received data into the scrolled text widget
        debug_text.insert(tk.END, last_data)
        # Autoscroll to the latest content
        debug_text.see(tk.END)
        debug_text.config(state=tk.DISABLED)
    
    # Schedule the next update
    dbug.after(2000, update_debug_text)

#Function to handle the delete session serial data 
def del_reading():
    global recieved_data
    global count
    global start_time
    start_time = "Nil"
    stop_reading()
    received_data = ""
    count = 0
    messagebox.showinfo("Deleted Session Data","Deleted Session Data Successfully!")

# Function to handle the save button click
def on_save_button_click():
    save_to_file()

def open_about_window():
    global about_window
    if about_window is None or not about_window.winfo_exists():
        about_window = tk.Toplevel(window)
        about_window.title("PLANKTON > ABOUT")
        about_window.geometry('300x150+100+100')
        about_window.resizable(False, False)
    else:
        about_window.lift()

    about_label = tk.Label(about_window, text="PLANKTON CONTROL PANEL\nVersion 1.1\n\nCreated by\nThe OG Students @ KVSAP")
    about_label.pack(pady=20)

def helpme():
    help_file_path = 'help/help.html'
    webbrowser.open(help_file_path)
    

# Function to close the program
def exit_program():
    if dbug and dbug.winfo_exists():
        dbug.destroy()
    if about_window and about_window.winfo_exists():
        about_window.destroy()
    if feedback_window and feedback_window.winfo_exists():
        feedback_window.destroy()
    window.destroy()
    
def on_exit_button_click():
    result = messagebox.askquestion("Exit", "Are you sure to quit?")
    if result == 'yes':
        exit_program()
        
def on_del_button_click():
    result = messagebox.askquestion("Delete Session Data", "Are you sure to delete current session data?")
    if result == 'yes':
        del_reading()
        
def send_feedback():
    global feedback_window
    if feedback_window is None or not feedback_window.winfo_exists():
        feedback_window = tk.Toplevel(window)
        feedback_window.title("PLANKTON > ABOUT")
        feedback_window.geometry('420x260+100+100')
        feedback_window.resizable(False, False)
    else:
        feedback_window.lift()
    tk.Label(feedback_window, text="Name: ").place(x=1, y=1)
    tk.Label(feedback_window, text="Email: ").place(x=1, y=30)
    tk.Label(feedback_window, text="Description (optional): ").place(x=1, y=60)
    cname=tk.StringVar()
    cname_entry = ttk.Entry(feedback_window, textvariable=cname, width=55)
    cname_entry.place(x=50,y=3)
    cemail=tk.StringVar()
    cemail_entry = ttk.Entry(feedback_window, textvariable=cemail, width=55)
    cemail_entry.place(x=50,y=30)
    des_text = scrolledtext.ScrolledText(feedback_window, wrap=tk.WORD, width=50, height=8)
    des_text.place(x=0, y=80)
    
    def on_send_button():
        res = messagebox.askquestion("Send Feedback", "Are you sure to send feedback?")
        if res == 'yes':
            #print("send")
            sname = cname.get()
            email = cemail.get()
            sdes = des_text.get("1.0","end")
            webhook = DiscordWebhook(url='https://discord.com/api/webhooks/1189887053165510676/YBJaB0LyG9m2ZbmrH3_r2aASyjB6Sg-u0XxtyFCaJjl0HNoc3lTvUJ0CeE4U44WTtCMx', username="PLANKTON > SUPPORT")
            embed = DiscordEmbed(title=email, description=sdes)
            embed.set_author(name=sname)
            embed.set_footer(text=time.strftime("%H:%M:%S-%d/%m/%Y"))
            embed.set_color('20a830')
            webhook.add_embed(embed)
            try:
                webhook.execute()
                messagebox.showinfo("Thank You!", "Thank you so much for sending a feedback!\nWhether it is good or bad, we will reach out to you soon!")
                feedback_window.destroy()
            except:
                #print("failed")
                messagebox.showerror("Error!", "Can't send feedback right now!\nPlease try again later!")
                feedback_window.lift()
        else:
            feedback_window.lift()
    def on_cancel_button():
        res = messagebox.askquestion("Cancel Feedback", "Are you sure to cancel sending feedback?")
        if res == 'yes':
            feedback_window.destroy()
        else:
            feedback_window.lift()
    
    send_button = ttk.Button(feedback_window, text="Send Feedback", command=on_send_button)
    send_button.place(x=100,y=220)
    cancel_button = ttk.Button(feedback_window, text="Cancel", command=on_cancel_button)
    cancel_button.place(x=240,y=220)
    
# Create Menubar and add items to it
file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)

file_menu.add_command(label="Start Reading", command=read_serial)
file_menu.add_command(label="Stop Reading", command=stop_reading)
file_menu.add_command(label="Save to File", command=on_save_button_click, accelerator="Ctrl+S")
file_menu.add_command(label="Exit", command=on_exit_button_click, accelerator="Ctrl+Q")

edit_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Edit", menu=edit_menu)

edit_menu.add_command(label="Delete Session Data", command=on_del_button_click, accelerator="Ctrl+D")

com_ports_menu = tk.Menu(edit_menu, tearoff=0)
edit_menu.add_cascade(label=f"Select COM Port: {selected_com_port.get()}", menu=com_ports_menu)

for index, port in enumerate(com_ports):
    com_ports_menu.add_command(label=port, command=lambda p=port: on_com_port_selected(p))

# Function to update submenu label dynamically
def update_com_ports_label():
    com_ports_submenu_label.set(f"Select COM Port: {selected_com_port.get()}")
    edit_menu.entryconfig(1, label=com_ports_submenu_label.get())

# Trace changes in the StringVar
selected_com_port.trace_add('write', lambda *args: update_com_ports_label())

advan_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Advanced", menu=advan_menu)

advan_menu.add_command(label="Debug", command=debug)
advan_menu.add_command(label="Quick Calibrate Moisture", command=calibrate_moisture)

help_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="Help", menu=help_menu)

help_menu.add_command(label="Help Contents", command=helpme, accelerator="Ctrl+H")
help_menu.add_command(label="Send Feedback", command=send_feedback)
help_menu.add_command(label="About PLANKTON", command=open_about_window)

window.bind_all("<Control-s>", lambda event: save_to_file())
window.bind_all("<Control-q>", lambda event: on_exit_button_click())
window.bind_all("<Control-h>", lambda event: helpme())
window.bind_all("<Control-d>", lambda event: on_del_button_click())

# Create buttons and pack them into the window
start_button = ttk.Button(window, text="  Start  ", command=read_serial)
start_button.place(x=310,y=160)
ToolTip(start_button, "Start reading data from the device")

stop_button = ttk.Button(window, text="  Stop  ", command=stop_reading, state=tk.DISABLED)
stop_button.place(x=310,y=200)
ToolTip(stop_button, "Stop reading data from the device")

del_button = ttk.Button(window, text="Delete Session Data", command=on_del_button_click)
del_button.place(x=292,y=240)
ToolTip(del_button, "Delete current session data")

save_button = ttk.Button(window, text="Save to File", command=on_save_button_click)
save_button.place(x=310,y=280)
ToolTip(save_button, "Save current session data to file")

exit_button = ttk.Button(window, text="  Exit  ", command=on_exit_button_click)
exit_button.place(x=310,y=320)
ToolTip(exit_button, "Close program")

window.protocol("WM_DELETE_WINDOW", exit_program)

# Run the Tkinter event loop
window.mainloop()
