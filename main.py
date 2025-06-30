import time
import tkinter as tk
from tkinter import ttk, messagebox
from screeninfo import get_monitors
import pygetwindow as gw


def get_monitors_with_names():
    monitors = get_monitors()
    monitor_labels = []
    for i, m in enumerate(monitors):
        label = f"Monitor {i + 1} ({m.width}x{m.height} @ {m.x},{m.y})"
        monitor_labels.append((i, label))
    return monitor_labels, monitors


def get_window_titles():
    return [w for w in gw.getAllWindows() if w.title.strip() and w.visible]


def rect_intersection_area(r1, r2):
    x1 = max(r1[0], r2[0])
    y1 = max(r1[1], r2[1])
    x2 = min(r1[0] + r1[2], r2[0] + r2[2])
    y2 = min(r1[1] + r1[3], r2[1] + r2[3])

    width = max(0, x2 - x1)
    height = max(0, y2 - y1)
    return width * height


def find_monitor_for_window(window, monitors):
    wx, wy, ww, wh = window.left, window.top, window.width, window.height
    window_rect = (wx, wy, ww, wh)
    max_area = 0
    best_monitor_index = None

    for i, m in enumerate(monitors):
        monitor_rect = (m.x, m.y, m.width, m.height)
        area = rect_intersection_area(window_rect, monitor_rect)
        if area > max_area:
            max_area = area
            best_monitor_index = i

    return best_monitor_index


class DisplayManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DisplayManager")
        self.geometry("700x450")
        self.minsize(500, 350)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        tk.Label(self, text="Wybierz monitor:").grid(row=0, column=0, sticky='w', padx=10, pady=(10, 0))
        self.monitor_labels, self.monitors = get_monitors_with_names()
        self.monitor_combobox = ttk.Combobox(self, values=[label for _, label in self.monitor_labels], state="readonly")
        if self.monitor_labels:
            self.monitor_combobox.current(0)
        self.monitor_combobox.grid(row=1, column=0, sticky='ew', padx=10)

        tk.Label(self, text="Filtruj okna:").grid(row=2, column=0, sticky='w', padx=10, pady=(10, 0))
        self.filter_entry = tk.Entry(self)
        self.filter_entry.grid(row=3, column=0, sticky='ew', padx=10, pady=(0, 5))
        self.filter_entry.bind('<KeyRelease>', lambda e: self.update_window_list())

        # Tabela z dwoma kolumnami: Okno | Monitor
        self.tree = ttk.Treeview(self, columns=("window", "monitor"), show='headings', selectmode='browse')
        self.tree.heading("window", text="Okno")
        self.tree.heading("monitor", text="Monitor")
        self.tree.column("window", anchor="w", width=400)
        self.tree.column("monitor", anchor="w", width=250)
        self.tree.grid(row=4, column=0, sticky='nsew', padx=10, pady=5)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=4, column=1, sticky='ns')
        self.tree.configure(yscrollcommand=scrollbar.set)

        button_frame = tk.Frame(self)
        button_frame.grid(row=5, column=0, sticky='ew', padx=10, pady=10)
        button_frame.columnconfigure((0, 1, 2), weight=1)  # Zmieniono na 3 kolumny

        refresh_button = tk.Button(button_frame, text="Odśwież listę okien", command=self.update_window_list)
        refresh_button.grid(row=0, column=0, sticky='ew', padx=(0, 5))

        move_button = tk.Button(button_frame, text="Przenieś okno na monitor", command=self.move_window_to_monitor)
        move_button.grid(row=0, column=1, sticky='ew', padx=(5, 5))

        close_button = tk.Button(button_frame, text="Zamknij okno", command=self.close_window)
        close_button.grid(row=0, column=2, sticky='ew', padx=(5, 0))

        self.bind('<Return>', lambda event: self.move_window_to_monitor())

        self.windows_list = []
        self.filtered_windows_list = []

        self.update_window_list()

    def filter_windows(self, filter_text, windows):
        if not filter_text:
            return windows
        filter_text = filter_text.lower()
        return [w for w in windows if filter_text in w.title.lower()]

    def update_window_list(self, selected_hwnd=None):
        filter_text = self.filter_entry.get().strip()
        self.windows_list = get_window_titles()
        self.filtered_windows_list = self.filter_windows(filter_text, self.windows_list)

        self.tree.delete(*self.tree.get_children())

        selected_index = None
        for idx, w in enumerate(self.filtered_windows_list):
            monitor_idx = find_monitor_for_window(w, self.monitors)
            monitor_label = self.monitor_labels[monitor_idx][1] if monitor_idx is not None else "Nieznany monitor"

            self.tree.insert('', 'end', iid=str(idx), values=(w.title, monitor_label))

            if selected_hwnd is not None and w._hWnd == selected_hwnd:
                selected_index = idx

        if selected_index is not None:
            self.tree.selection_set(str(selected_index))
            self.tree.see(str(selected_index))

    def move_window_to_monitor(self):
        selected = self.tree.selection()
        monitor_index = self.monitor_combobox.current()

        if not selected:
            messagebox.showwarning("Uwaga", "Wybierz okno.")
            return
        if monitor_index == -1:
            messagebox.showwarning("Uwaga", "Wybierz monitor.")
            return

        selected_index = int(selected[0])
        selected_window = self.filtered_windows_list[selected_index]
        selected_monitor = self.monitors[monitor_index]
        selected_hwnd = selected_window._hWnd

        try:
            # Przywróć okno do normalnego rozmiaru
            selected_window.restore()
            time.sleep(0.2)

            # Przenieś chwilowo okno lekko poza monitor (10 px na lewo)
            selected_window.moveTo(selected_monitor.x - 10, selected_monitor.y)
            time.sleep(0.2)

            # Przenieś na właściwe miejsce
            selected_window.moveTo(selected_monitor.x, selected_monitor.y)
            time.sleep(0.2)

            # Zmień rozmiar okna na rozmiar monitora
            selected_window.resizeTo(selected_monitor.width, selected_monitor.height)
            time.sleep(0.2)

            # Aktywuj okno
            selected_window.activate()

            self.update_window_list(selected_hwnd)

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się przesunąć okna:\n{e}")

    def close_window(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning("Uwaga", "Wybierz okno do zamknięcia.")
            return

        selected_index = int(selected[0])
        selected_window = self.filtered_windows_list[selected_index]

        try:
            selected_window.close()
            messagebox.showinfo("Sukces", f"Okno '{selected_window.title}' zostało zamknięte.")
            self.update_window_list()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zamknąć okno:\n{e}")


if __name__ == "__main__":
    app = DisplayManagerApp()
    app.mainloop()
