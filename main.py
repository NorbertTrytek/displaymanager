import time
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from screeninfo import get_monitors
import pygetwindow as gw
import json
import os
import subprocess

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # Zmień ścieżkę jeśli trzeba
CONFIG_FILE = "saved_chrome_windows.json"

def get_monitors_with_names():
    monitors = get_monitors()
    monitor_labels = []
    for i, m in enumerate(monitors):
        label = f"Monitor {i + 1} ({m.width}x{m.height} @ {m.x},{m.y})"
        monitor_labels.append((i, label))
    return monitor_labels, monitors


def get_window_titles():
    # Używaj 'visible' (atrybut, nie metoda)
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
        self.geometry("800x500")
        self.minsize(600, 400)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)

        # Monitory
        tk.Label(self, text="Wybierz monitor:").grid(row=0, column=0, sticky='w', padx=10, pady=(10, 0))
        self.monitor_labels, self.monitors = get_monitors_with_names()
        self.monitor_combobox = ttk.Combobox(self, values=[label for _, label in self.monitor_labels], state="readonly")
        if self.monitor_labels:
            self.monitor_combobox.current(0)
        self.monitor_combobox.grid(row=1, column=0, sticky='ew', padx=10)

        # Filtr okien
        tk.Label(self, text="Filtruj okna:").grid(row=2, column=0, sticky='w', padx=10, pady=(10, 0))
        self.filter_entry = tk.Entry(self)
        self.filter_entry.grid(row=3, column=0, sticky='ew', padx=10, pady=(0, 5))
        self.filter_entry.bind('<KeyRelease>', lambda e: self.update_window_list())

        # Tabela okien
        self.tree = ttk.Treeview(self, columns=("window", "monitor"), show='headings', selectmode='browse')
        self.tree.heading("window", text="Okno")
        self.tree.heading("monitor", text="Monitor")
        self.tree.column("window", anchor="w", width=450)
        self.tree.column("monitor", anchor="w", width=300)
        self.tree.grid(row=5, column=0, sticky='nsew', padx=10, pady=5)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=5, column=1, sticky='ns')
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Przyciskowy panel
        button_frame = tk.Frame(self)
        button_frame.grid(row=6, column=0, sticky='ew', padx=10, pady=10)
        button_frame.columnconfigure((0, 1, 2, 3), weight=1)

        refresh_button = tk.Button(button_frame, text="Odśwież listę okien", command=self.update_window_list)
        refresh_button.grid(row=0, column=0, sticky='ew', padx=(0, 5))

        move_button = tk.Button(button_frame, text="Przenieś okno na monitor", command=self.move_window_to_monitor)
        move_button.grid(row=0, column=1, sticky='ew', padx=5)

        close_button = tk.Button(button_frame, text="Zamknij okno", command=self.close_window)
        close_button.grid(row=0, column=2, sticky='ew', padx=5)

        save_button = tk.Button(button_frame, text="Zapisz okno Chrome", command=self.save_chrome_window)
        save_button.grid(row=0, column=3, sticky='ew', padx=(5, 0))

        # Drugi panel na zapisane linki
        tk.Label(self, text="Zapisane linki Chrome:").grid(row=7, column=0, sticky='w', padx=10, pady=(10, 0))
        self.saved_links_tree = ttk.Treeview(self, columns=("url", "monitor"), show='headings', selectmode='browse')
        self.saved_links_tree.heading("url", text="URL")
        self.saved_links_tree.heading("monitor", text="Monitor")
        self.saved_links_tree.column("url", anchor="w", width=450)
        self.saved_links_tree.column("monitor", anchor="w", width=300)
        self.saved_links_tree.grid(row=8, column=0, sticky='nsew', padx=10, pady=5)

        scrollbar2 = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.saved_links_tree.yview)
        scrollbar2.grid(row=8, column=1, sticky='ns')
        self.saved_links_tree.configure(yscrollcommand=scrollbar2.set)

        # Przyciski przywracania i usuwania
        bottom_button_frame = tk.Frame(self)
        bottom_button_frame.grid(row=9, column=0, sticky='ew', padx=10, pady=10)
        bottom_button_frame.columnconfigure((0,1), weight=1)

        restore_button = tk.Button(bottom_button_frame, text="Przywróć zapisane okna Chrome", command=self.restore_chrome_windows)
        restore_button.grid(row=0, column=0, sticky='ew', padx=(0,5))

        delete_button = tk.Button(bottom_button_frame, text="Usuń zaznaczony zapis", command=self.delete_saved_link)
        delete_button.grid(row=0, column=1, sticky='ew', padx=(5,0))

        self.bind('<Return>', lambda event: self.move_window_to_monitor())

        self.windows_list = []
        self.filtered_windows_list = []

        self.entries = []  # lista zapisanych linków i monitorów
        self.load_saved_entries()

        self.update_window_list()
        self.update_saved_links_list()

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
            selected_window.restore()
            time.sleep(0.2)
            selected_window.activate()
            time.sleep(0.2)
            selected_window.moveTo(selected_monitor.x, selected_monitor.y)
            time.sleep(0.2)
            selected_window.resizeTo(selected_monitor.width, selected_monitor.height)
            time.sleep(0.2)
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

    def save_chrome_window(self):
        # Dodaj URL i monitor do listy zapisanych wpisów
        # Pytamy o URL przez dialog
        url = simpledialog.askstring("Dodaj link Chrome", "Podaj URL (np. https://www.google.com):", parent=self)
        if not url:
            return

        monitor_index = self.monitor_combobox.current()
        if monitor_index == -1:
            messagebox.showwarning("Uwaga", "Wybierz monitor przed zapisem.")
            return

        self.entries.append({"url": url, "monitor_index": monitor_index})
        self.save_entries()
        self.update_saved_links_list()
        messagebox.showinfo("Sukces", f"Zapisano link {url} na {self.monitor_labels[monitor_index][1]}")

    def update_saved_links_list(self):
        self.saved_links_tree.delete(*self.saved_links_tree.get_children())
        for i, entry in enumerate(self.entries):
            url = entry["url"]
            monitor_label = self.monitor_labels[entry["monitor_index"]][1] if entry["monitor_index"] < len(self.monitor_labels) else "Nieznany monitor"
            self.saved_links_tree.insert('', 'end', iid=str(i), values=(url, monitor_label))

    def save_entries(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.entries, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać pliku konfiguracyjnego:\n{e}")

    def load_saved_entries(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.entries = json.load(f)
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się wczytać pliku konfiguracyjnego:\n{e}")

    def restore_chrome_windows(self):
        if not self.entries:
            messagebox.showinfo("Informacja", "Brak zapisanych linków do przywrócenia.")
            return

        restored_count = 0

        # Pobierz aktualne okna chrome przed otwarciem linków
        windows_before = {w._hWnd for w in get_window_titles() if "chrome" in w.title.lower()}

        for entry in self.entries:
            url = entry["url"]
            try:
                subprocess.Popen([CHROME_PATH, "--new-window", url])
                restored_count += 1
                time.sleep(3)  # daj chwilę na otwarcie okna
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się uruchomić Chrome z linkiem {url}:\n{e}")

        time.sleep(1)

        windows_after = {w._hWnd for w in get_window_titles() if "chrome" in w.title.lower()}
        new_windows_hwnds = list(windows_after - windows_before)

        windows = {w._hWnd: w for w in get_window_titles()}

        # Przesuń nowe okna w kolejności wpisów
        for i, entry in enumerate(self.entries):
            if i >= len(new_windows_hwnds):
                break
            hwnd = new_windows_hwnds[i]
            w = windows.get(hwnd)
            if w:
                monitor = self.monitors[entry["monitor_index"]]
                try:
                    w.restore()
                    time.sleep(0.2)
                    w.activate()
                    time.sleep(0.2)
                    w.moveTo(monitor.x, monitor.y)
                    time.sleep(0.2)
                    w.resizeTo(monitor.width, monitor.height)
                    time.sleep(0.2)
                except Exception as e:
                    print(f"Nie udało się przesunąć okna Chrome (hwnd {hwnd}): {e}")

        messagebox.showinfo("Informacja", f"Otworzono i przeniesiono {restored_count} linków Chrome.")

    def delete_saved_link(self):
        selected = self.saved_links_tree.selection()
        if not selected:
            messagebox.showwarning("Uwaga", "Wybierz zapisany link do usunięcia.")
            return
        index = int(selected[0])
        del self.entries[index]
        self.save_entries()
        self.update_saved_links_list()


if __name__ == "__main__":
    app = DisplayManagerApp()
    app.mainloop()
