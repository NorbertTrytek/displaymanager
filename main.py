import tkinter as tk
from tkinter import ttk, messagebox
from screeninfo import get_monitors
import pygetwindow as gw
import wmi

def get_windows_monitors():
    try:
        w = wmi.WMI(namespace='root\\wmi')
        monitors = w.WmiMonitorID()
        names = []
        for m in monitors:
            name = ''.join(chr(c) for c in m.UserFriendlyName if c != 0)
            names.append(name)
        return names
    except Exception as e:
        print(f"WMI error: {e}")
        return []

def get_monitors_with_names():
    monitors = get_monitors()
    wmi_monitors = get_windows_monitors()

    monitor_labels = []
    for i, m in enumerate(monitors):
        label = f"Monitor {i + 1}"
        if i < len(wmi_monitors) and wmi_monitors[i]:
            label = wmi_monitors[i]
        label += f" ({m.width}x{m.height} @ {m.x},{m.y})"
        monitor_labels.append((i, label))
    return monitor_labels, monitors

def get_window_titles():
    windows = gw.getAllWindows()
    window_list = []
    for w in windows:
        if w.title.strip() != '' and w.visible:
            window_list.append(w)
    return window_list

def filter_windows(filter_text, windows):
    if not filter_text:
        return windows
    filter_text = filter_text.lower()
    return [w for w in windows if filter_text in w.title.lower()]

def update_window_list():
    global windows_list, filtered_windows_list
    filter_text = filter_entry.get().strip()

    all_windows = get_window_titles()
    windows_list = all_windows
    filtered_windows_list = filter_windows(filter_text, windows_list)

    listbox_windows.delete(0, tk.END)
    for w in filtered_windows_list:
        listbox_windows.insert(tk.END, w.title)

def move_window_to_monitor():
    selection = listbox_windows.curselection()
    monitor_index = monitor_combobox.current()

    if not selection:
        messagebox.showwarning("Uwaga", "Wybierz okno.")
        return
    if monitor_index == -1:
        messagebox.showwarning("Uwaga", "Wybierz monitor.")
        return

    window_index = selection[0]
    selected_window = filtered_windows_list[window_index]
    _, monitors = get_monitors_with_names()
    selected_monitor = monitors[monitor_index]

    try:
        selected_window.moveTo(selected_monitor.x, selected_monitor.y)
        selected_window.resizeTo(selected_monitor.width, selected_monitor.height)
        selected_window.activate()
    except Exception as e:
        messagebox.showerror("Błąd", f"Nie udało się przesunąć okna:\n{e}")

# GUI
root = tk.Tk()
root.title("DisplayManager")  # tutaj zmiana tytułu aplikacji
root.geometry("700x450")
root.minsize(500, 350)

root.columnconfigure(0, weight=1)
root.rowconfigure(4, weight=1)

tk.Label(root, text="Wybierz monitor:").grid(row=0, column=0, sticky='w', padx=10, pady=(10, 0))
monitor_labels, _ = get_monitors_with_names()
monitor_combobox = ttk.Combobox(root, values=[m[1] for m in monitor_labels], state="readonly")
if monitor_labels:
    monitor_combobox.current(0)
monitor_combobox.grid(row=1, column=0, sticky='ew', padx=10)

tk.Label(root, text="Filtruj okna:").grid(row=2, column=0, sticky='w', padx=10, pady=(10, 0))
filter_entry = tk.Entry(root)
filter_entry.grid(row=3, column=0, sticky='ew', padx=10, pady=(0, 5))
filter_entry.bind('<KeyRelease>', lambda e: update_window_list())

frame_listbox = tk.Frame(root)
frame_listbox.grid(row=4, column=0, sticky='nsew', padx=10)
root.rowconfigure(4, weight=1)

scrollbar = tk.Scrollbar(frame_listbox, orient=tk.VERTICAL)
listbox_windows = tk.Listbox(frame_listbox, yscrollcommand=scrollbar.set)
scrollbar.config(command=listbox_windows.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
listbox_windows.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

button_frame = tk.Frame(root)
button_frame.grid(row=5, column=0, sticky='ew', padx=10, pady=10)
button_frame.columnconfigure((0,1), weight=1)

refresh_button = tk.Button(button_frame, text="Odśwież listę okien", command=update_window_list)
refresh_button.grid(row=0, column=0, sticky='ew', padx=(0, 5))

move_button = tk.Button(button_frame, text="Przenieś okno na monitor", command=move_window_to_monitor)
move_button.grid(row=0, column=1, sticky='ew', padx=(5, 0))

root.bind('<Return>', lambda event: move_window_to_monitor())

windows_list = []
filtered_windows_list = []

update_window_list()

root.mainloop()