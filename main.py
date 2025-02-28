import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import keyboard
import pyperclip
import time
import pygetwindow as gw
import pyautogui
import re
import json
from typing import Optional, List

global_strings: List[str] = ["Пример строки 1", "Пример строки 2", "Пример строки 3"]

class StringListApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("String List")
        self.root.geometry("400x300")
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.data_file = "strings.json"
        self.strings = self.load_strings()
        
        # Меню
        self.menu_bar = tk.Menu(root)
        
        # Меню Файл
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Выход", command=root.destroy)
        self.menu_bar.add_cascade(label="Файл", menu=self.file_menu)
        
        # Меню Поиск
        self.search_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.exact_match_var = tk.BooleanVar()
        self.case_sensitive_var = tk.BooleanVar()
        self.keep_search_var = tk.BooleanVar()
        self.regex_pattern_var = tk.BooleanVar()
        
        self.search_menu.add_checkbutton(
            label="Точное совпадение", 
            variable=self.exact_match_var,
            command=self.update_list
        )
        self.search_menu.add_checkbutton(
            label="Учитывать регистр", 
            variable=self.case_sensitive_var,
            command=self.update_list
        )
        self.search_menu.add_checkbutton(
            label="Сохранять условия поиска", 
            variable=self.keep_search_var
        )
        self.search_menu.add_separator()
        self.search_menu.add_checkbutton(
            label="Режим регулярных выражений", 
            variable=self.regex_pattern_var,
            command=self.update_list
        )
        self.menu_bar.add_cascade(label="Поиск", menu=self.search_menu)
        
        # Меню Вид
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.always_on_top_var = tk.BooleanVar(value=True)
        self.view_menu.add_checkbutton(
            label="Поверх всех окон", 
            variable=self.always_on_top_var,
            command=self.toggle_always_on_top
        )
        self.menu_bar.add_cascade(label="Вид", menu=self.view_menu)

        # Меню Справка
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Шпаргалка по Regex", command=self.show_regex_help)
        self.help_menu.add_command(label="О программе", command=self.show_about)
        self.menu_bar.add_cascade(label="Справка", menu=self.help_menu)
        
        root.config(menu=self.menu_bar)

        # Основные элементы интерфейса
        self.filtered_strings: List[str] = self.strings.copy()
        self.previous_window: Optional[gw.Win32Window] = None
        self.editing_index: Optional[int] = None

        self.filter_var = tk.StringVar()
        self.filter_var.trace("w", lambda *args: self.update_list())
        
        input_frame = ttk.Frame(root)
        input_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.entry = ttk.Entry(input_frame, textvariable=self.filter_var)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.listbox = tk.Listbox(root)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.update_list()

        # Кнопки управления
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

        # Привязка событий
        self.listbox.bind("<Return>", self.insert_string)
        self.listbox.bind("<Double-Button-1>", self.insert_string)
        self.root.bind("<Escape>", self.hide_window)
        self.listbox.bind("<Button-3>", self.show_context_menu)

    def load_strings(self) -> List[str]:
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return global_strings.copy()

    def save_strings(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.strings, f, ensure_ascii=False, indent=2)

    def show_context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Копировать", command=self.copy_to_clipboard)
        menu.add_command(label="Удалить", command=self.delete_string)
        menu.tk_popup(event.x_root, event.y_root)

    def copy_to_clipboard(self):
        if self.listbox.curselection():
            index = self.listbox.curselection()[0]
            selected = self.filtered_strings[index]
            pyperclip.copy(selected)

    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("О программе")
        about_window.geometry("300x200")
        
        info_text = ("String List\n\n"
                    "Версия 1.1\n"
                    "Автор: Ваше имя\n"
                    "Лицензия: MIT\n\n"
                    "Программа для быстрой вставки\n"
                    "часто используемых строковых шаблонов")
        
        ttk.Label(about_window, text=info_text, justify=tk.LEFT, padding=10).pack(expand=True)
        ttk.Button(about_window, text="OK", command=about_window.destroy).pack(pady=10)

    def show_regex_help(self):
        help_text = """Шпаргалка по регулярным выражениям..."""
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Справка по регулярным выражениям")
        help_window.geometry("500x400")
        
        text_area = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_area.insert(tk.INSERT, help_text)
        text_area.configure(state='disabled')

    def update_list(self, *args: tk.Event) -> None:
        """Обновляет список строк согласно параметрам поиска"""
        filter_text = self.filter_var.get()
        
        if self.regex_pattern_var.get():
            try:
                flags = 0 if self.case_sensitive_var.get() else re.IGNORECASE
                pattern = re.compile(filter_text, flags)
                self.filtered_strings = [s for s in self.strings if pattern.search(s)]
            except re.error:
                self.filtered_strings = self.strings.copy()
        else:
            case_sensitive = self.case_sensitive_var.get()
            compare_text = filter_text if case_sensitive else filter_text.lower()
            compare_strings = self.strings if case_sensitive else [s.lower() for s in self.strings]

            if self.exact_match_var.get():
                # Поиск точного вхождения всей фразы
                self.filtered_strings = [
                    s for s, cs in zip(self.strings, compare_strings)
                    if compare_text in cs
                ]
            else:
                # Обычный поиск по всем словам
                filter_words = compare_text.split()
                self.filtered_strings = [
                    s for s, cs in zip(self.strings, compare_strings)
                    if all(word in cs for word in filter_words)
                ]
            
        self.listbox.delete(0, tk.END)
        for s in self.filtered_strings:
            self.listbox.insert(tk.END, s)

    def insert_string(self, event: Optional[tk.Event] = None) -> None:
        """Вставляет выбранную строку в активное окно"""
        selected = self.listbox.curselection()
        if selected:
            selected_string = self.filtered_strings[selected[0]]
            pyperclip.copy(selected_string)
            self.hide_window()
            time.sleep(0.1)
            if self.previous_window:
                try:
                    self.previous_window.activate()
                    keyboard.press_and_release("ctrl+v")
                except Exception as e:
                    print(f"Ошибка активации окна: {e}")

    def hide_window(self, event: Optional[tk.Event] = None) -> None:
        """Скрывает окно приложения"""
        if not self.keep_search_var.get():
            self.filter_var.set("")
            self.update_list()
        self.root.withdraw()
        if self.previous_window:
            try:
                self.previous_window.activate()
            except Exception as e:
                print(f"Ошибка активации предыдущего окна: {e}")

    def add_string(self) -> None:
        """Добавляет новую строку в список"""
        new_string = self.filter_var.get().strip()
        if new_string and new_string not in self.strings:
            self.strings.append(new_string)
            self.save_strings()
            self.update_list()
            self.filter_var.set("")
            self.entry.focus()

    def edit_string(self) -> None:
        """Начинает редактирование выбранной строки"""
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

    def save_edit(self) -> None:
        """Сохраняет отредактированную строку"""
        if self.editing_index is not None:
            new_string = self.filter_var.get().strip()
            if new_string and new_string not in self.strings:
                self.strings[self.editing_index] = new_string
                self.save_strings()
            self.cleanup_edit()

    def cancel_edit(self) -> None:
        """Отменяет редактирование"""
        self.cleanup_edit()

    def cleanup_edit(self) -> None:
        """Восстанавливает интерфейс после редактирования"""
        self.ok_button.pack_forget()
        self.cancel_button.pack_forget()
        self.add_button.pack(side=tk.LEFT, padx=5)
        self.edit_button.pack(side=tk.LEFT, padx=5)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        self.filter_var.set("")
        self.update_list()
        self.editing_index = None
        self.entry.focus()

    def delete_string(self) -> None:
        """Удаляет выбранную строку"""
        selected = self.listbox.curselection()
        if selected:
            selected_string = self.filtered_strings[selected[0]]
            self.strings.remove(selected_string)
            self.save_strings()
            self.update_list()
            self.entry.focus()

    def toggle_always_on_top(self) -> None:
        """Переключает режим 'Поверх всех окон'"""
        self.root.attributes("-topmost", self.always_on_top_var.get())

def show_window() -> None:
    """Показывает окно приложения"""
    app.previous_window = gw.getActiveWindow()
    x, y = pyautogui.position()
    app.root.geometry(f"+{x}+{y}")
    app.root.deiconify()
    app.root.attributes("-topmost", app.always_on_top_var.get())
    app.root.lift()
    app.root.focus_force()
    app.entry.focus()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = StringListApp(root)
    keyboard.add_hotkey("ctrl+alt+s", show_window)
    root.mainloop()