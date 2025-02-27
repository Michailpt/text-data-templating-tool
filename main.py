import tkinter as tk
from tkinter import ttk
import keyboard
import pyperclip
import time
import pygetwindow as gw

# Глобальный список строк
global_strings = ["Пример строки 1", "Пример строки 2", "Пример строки 3"]

class StringListApp:
    def __init__(self, root, previous_window):
        self.root = root
        self.previous_window = previous_window  # Запоминаем предыдущее активное окно
        self.root.title("String List")
        self.root.geometry("400x300")
        self.root.attributes("-topmost", True)

        self.strings = global_strings
        self.filtered_strings = self.strings.copy()

        self.filter_var = tk.StringVar()
        self.filter_var.trace("w", self.update_list)

        self.entry = ttk.Entry(root, textvariable=self.filter_var)
        self.entry.pack(pady=10, padx=10, fill=tk.X)
        self.entry.focus()

        self.listbox = tk.Listbox(root)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.update_list()

        self.button_frame = ttk.Frame(root)
        self.button_frame.pack(pady=10)

        self.add_button = ttk.Button(self.button_frame, text="Добавить", command=self.add_string)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.edit_button = ttk.Button(self.button_frame, text="Изменить", command=self.edit_string)
        self.edit_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = ttk.Button(self.button_frame, text="Удалить", command=self.delete_string)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        self.ok_button = ttk.Button(self.button_frame, text="OK", command=self.save_edit)
        self.cancel_button = ttk.Button(self.button_frame, text="Отмена", command=self.cancel_edit)

        self.listbox.bind("<Return>", self.insert_string)
        self.listbox.bind("<Double-Button-1>", self.insert_string)

        self.editing_index = None

    def update_list(self, *args):
        filter_text = self.filter_var.get().lower()
        self.filtered_strings = [s for s in self.strings if filter_text in s.lower()]
        self.listbox.delete(0, tk.END)
        for s in self.filtered_strings:
            self.listbox.insert(tk.END, s)

    def add_string(self):
        new_string = self.filter_var.get().strip()
        if new_string and new_string not in self.strings:
            self.strings.append(new_string)
            self.update_list()
            self.filter_var.set("")
            self.entry.focus()

    def edit_string(self):
        selected = self.listbox.curselection()
        if selected:
            self.add_button.pack_forget()
            self.edit_button.pack_forget()
            self.delete_button.pack_forget()
            self.ok_button.pack(side=tk.LEFT, padx=5)
            self.cancel_button.pack(side=tk.LEFT, padx=5)
            self.editing_index = self.strings.index(self.filtered_strings[selected[0]])
            self.filter_var.set(self.strings[self.editing_index])
            self.entry.focus()

    def save_edit(self):
        if self.editing_index is not None:
            new_string = self.filter_var.get().strip()
            if new_string and new_string not in self.strings:
                self.strings[self.editing_index] = new_string
            self.cleanup_edit()

    def cancel_edit(self):
        self.cleanup_edit()

    def cleanup_edit(self):
        self.ok_button.pack_forget()
        self.cancel_button.pack_forget()
        self.add_button.pack(side=tk.LEFT, padx=5)
        self.edit_button.pack(side=tk.LEFT, padx=5)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        self.filter_var.set("")
        self.update_list()
        self.editing_index = None
        self.entry.focus()

    def delete_string(self):
        selected = self.listbox.curselection()
        if selected:
            selected_string = self.filtered_strings[selected[0]]
            self.strings.remove(selected_string)
            self.update_list()
            self.entry.focus()

    def insert_string(self, event):
        selected = self.listbox.curselection()
        if selected:
            selected_string = self.filtered_strings[selected[0]]
            pyperclip.copy(selected_string)  # Копируем в буфер обмена
            self.root.destroy()
            time.sleep(0.1)  # Короткая пауза для переключения фокуса
            if self.previous_window:
                self.previous_window.activate()
                keyboard.press_and_release("ctrl+v")  # Вставка через Ctrl+V

def show_window():
    previous_window = gw.getActiveWindow()  # Запоминаем активное окно
    root = tk.Tk()
    app = StringListApp(root, previous_window)
    root.mainloop()

keyboard.add_hotkey("ctrl+alt+s", show_window)
keyboard.wait("esc")
