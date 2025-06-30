import time
import tkinter as tk
from tkinter import ttk, messagebox
from screeninfo import get_monitors
import pygetwindow as gw
import json
import os
import subprocess
import shutil

SAVE_FILE = "saved_chrome_links.json"


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


class AddLinkDialog(tk.Toplevel):
    def __init__(self, parent, monitor_labels):
        super().__init__(parent)
        self.title("Dodaj link Chrome")
        self.geometry("400x150")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.result = None

        tk.Label(self, text="Podaj URL:").pack(pady=(10, 0))
        self.url_entry = tk.Entry(self, width=50)
        self.url_entry.pack(pady=(0, 10))
        self.url_entry.focus_set()

        tk.Label(self, text="Wybierz monitor:").pack()
        self.monitor_var = tk.StringVar()
        self.monitor_combobox = ttk.Combobox(
            self, values=[label for _, label in monitor_labels], textvariable=self.monitor_var, state="readonly"
        )
        if monitor_labels:
            self.monitor_combobox.current(0)
        self.monitor_combobox.pack(pady=(0, 10))

        button_frame = tk.Frame(self)
        button_frame.pack()

        save_btn = tk.Button(button_frame, text="Zapisz", width=10, command=self.on_save)
        save_btn.grid(row=0, column=0, padx=5)

        cancel_btn = tk.Button(button_frame, text="Anuluj", width=10, command=self.on_cancel)
        cancel_btn.grid(row=0, column=1, padx=5)

        self.bind("<Return>", lambda e: self.on_save())
        self.bind("<Escape>", lambda e: self.on_cancel())

    def on_save(self):
        url = self.url_entry.get().strip()
        monitor = self.monitor_combobox.current()
        if not url:
            messagebox.showwarning("Uwaga", "Podaj poprawny URL.")
            return
        if monitor == -1:
            messagebox.showwarning("Uwaga", "Wybierz monitor.")
            return
        self.result = (url, monitor)
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


def find_chrome_executable():
    # Standardowe lokalizacje chrome.exe na Windows
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    # Spróbuj znaleźć w PATH (może zwrócić None)
    return shutil.which("chrome")


class DisplayManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DisplayManager")
        self.geometry("700x500")
        self.minsize(500, 400)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        self.rowconfigure(6, weight=1)

        tk.Label(self, text="Wybierz monitor:").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))
        self.monitor_labels, self.monitors = get_monitors_with_names()
        self.monitor_combobox = ttk.Combobox(
            self, values=[label for _, label in self.monitor_labels], state="readonly"
        )
        if self.monitor_labels:
            self.monitor_combobox.current(0)
        self.monitor_combobox.grid(row=1, column=0, sticky="ew", padx=10)

        tk.Label(self, text="Filtruj okna:").grid(row=2, column=0, sticky="w", padx=10, pady=(10, 0))
        self.filter_entry = tk.Entry(self)
        self.filter_entry.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 5))
        self.filter_entry.bind("<KeyRelease>", lambda e: self.update_window_list())

        self.tree = ttk.Treeview(self, columns=("window", "monitor"), show="headings", selectmode="browse")
        self.tree.heading("window", text="Okno")
        self.tree.heading("monitor", text="Monitor")
        self.tree.column("window", anchor="w", width=400)
        self.tree.column("monitor", anchor="w", width=250)
        self.tree.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=4, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        button_frame = tk.Frame(self)
        button_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=10)
        button_frame.columnconfigure((0, 1, 2), weight=1)

        refresh_button = tk.Button(button_frame, text="Odśwież listę okien", command=self.update_window_list)
        refresh_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        move_button = tk.Button(button_frame, text="Przenieś okno na monitor", command=self.move_window_to_monitor)
        move_button.grid(row=0, column=1, sticky="ew", padx=5)

        close_button = tk.Button(button_frame, text="Zamknij okno", command=self.close_window)
        close_button.grid(row=0, column=2, sticky="ew", padx=(5, 0))

        save_restore_frame = tk.LabelFrame(self, text="Zarządzanie linkami Chrome")
        save_restore_frame.grid(row=6, column=0, sticky="nsew", padx=10, pady=10)
        save_restore_frame.columnconfigure(0, weight=1)
        save_restore_frame.rowconfigure(1, weight=1)

        self.saved_links_listbox = tk.Listbox(save_restore_frame)
        self.saved_links_listbox.grid(row=1, column=0, sticky="nsew", pady=(5, 5))

        btn_frame = tk.Frame(save_restore_frame)
        btn_frame.grid(row=2, column=0, sticky="ew")
        btn_frame.columnconfigure((0, 1, 2), weight=1)

        add_link_button = tk.Button(btn_frame, text="Dodaj link Chrome", command=self.save_chrome_window)
        add_link_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        restore_links_button = tk.Button(btn_frame, text="Przywróć zapisane linki", command=self.restore_saved_links)
        restore_links_button.grid(row=0, column=1, sticky="ew", padx=5)

        delete_link_button = tk.Button(btn_frame, text="Usuń zaznaczony link", command=self.delete_selected_link)
        delete_link_button.grid(row=0, column=2, sticky="ew", padx=(5, 0))

        self.windows_list = []
        self.filtered_windows_list = []
        self.entries = []

        self.load_entries()
        self.update_saved_links_list()
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

            self.tree.insert("", "end", iid=str(idx), values=(w.title, monitor_label))

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

            selected_window.moveTo(selected_monitor.x - 10, selected_monitor.y)
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
        dialog = AddLinkDialog(self, self.monitor_labels)
        self.wait_window(dialog)
        if dialog.result:
            url, monitor_index = dialog.result
            self.entries.append({"url": url, "monitor_index": monitor_index})
            self.save_entries()
            self.update_saved_links_list()
            messagebox.showinfo("Sukces", f"Zapisano link {url} na {self.monitor_labels[monitor_index][1]}")

    def update_saved_links_list(self):
        self.saved_links_listbox.delete(0, tk.END)
        for entry in self.entries:
            monitor_label = self.monitor_labels[entry["monitor_index"]][1] if 0 <= entry["monitor_index"] < len(self.monitor_labels) else "Nieznany monitor"
            self.saved_links_listbox.insert(tk.END, f'{entry["url"]} [{monitor_label}]')

    def delete_selected_link(self):
        selection = self.saved_links_listbox.curselection()
        if not selection:
            messagebox.showwarning("Uwaga", "Wybierz link do usunięcia.")
            return
        index = selection[0]
        del self.entries[index]
        self.save_entries()
        self.update_saved_links_list()

    def save_entries(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.entries, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać pliku: {e}")

    def load_entries(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    self.entries = json.load(f)
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się wczytać pliku: {e}")
                self.entries = []

    def restore_saved_links(self):
        chrome_path = find_chrome_executable()
        if not chrome_path:
            messagebox.showerror("Błąd", "Nie znaleziono pliku chrome.exe. Upewnij się, że Chrome jest zainstalowany.")
            return

        for entry in self.entries:
            url = entry["url"]
            monitor_index = entry["monitor_index"]

            if not (0 <= monitor_index < len(self.monitors)):
                messagebox.showwarning("Uwaga", f"Niepoprawny monitor dla linku {url}, pomijam.")
                continue

            monitor = self.monitors[monitor_index]

            try:
                args = [chrome_path, "--new-window", url]
                subprocess.Popen(args)
                time.sleep(2)  # Czekaj, aż okno się otworzy

                chrome_windows = [w for w in gw.getAllWindows() if "Chrome" in w.title]
                newest_window = max(chrome_windows, key=lambda w: w._hWnd, default=None)

                if newest_window:
                    newest_window.moveTo(monitor.x, monitor.y)
                    time.sleep(0.2)
                    newest_window.resizeTo(monitor.width, monitor.height)
                    time.sleep(0.2)
                    newest_window.activate()

            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się uruchomić linku {url}:\n{e}")

        messagebox.showinfo("Gotowe", "Przywrócono wszystkie zapisane linki Chrome.")


if __name__ == "__main__":
    app = DisplayManagerApp()
    app.mainloop()
