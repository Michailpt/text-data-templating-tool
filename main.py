import tkinter as tk
from tkinter import ttk, scrolledtext
import keyboard
import pyperclip
import time
import pygetwindow as gw
import pyautogui
import re
from typing import Optional, List

global_strings: List[str] = ["Пример строки 1", "Пример строки 2", "Пример строки 3"]

class StringListApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("String List")
        self.root.geometry("400x300")
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        
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
        
        # Меню Справка
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Шпаргалка по Regex", command=self.show_regex_help)
        self.help_menu.add_command(label="О программе", command=self.show_about)  # Добавлена новая кнопка
        self.menu_bar.add_cascade(label="Справка", menu=self.help_menu)
        
        root.config(menu=self.menu_bar)

        # Основные элементы интерфейса
        self.strings: List[str] = global_strings
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

    def show_about(self):
        """Показывает окно 'О программе'"""
        about_window = tk.Toplevel(self.root)
        about_window.title("О программе")
        about_window.geometry("300x200")
        
        info_text = ("String List\n\n"
                    "Версия 1.0\n"
                    "Автор: Ваше имя\n"
                    "Лицензия: MIT\n\n"
                    "Программа для быстрой вставки\n"
                    "часто используемых строковых шаблонов")
        
        ttk.Label(about_window, text=info_text, justify=tk.LEFT, padding=10).pack(expand=True)
        ttk.Button(about_window, text="OK", command=about_window.destroy).pack(pady=10)

    def show_regex_help(self):
        """Показывает окно с шпаргалкой по регулярным выражениям"""
        help_text = """Шпаргалка по регулярным выражениям

Основные синтаксисы:
.    - Любой символ
^    - Начало строки
$    - Конец строки
\\d   - Цифра [0-9]
\\D   - Не цифра
\\w   - Буква, цифра или подчёркивание [a-zA-Z0-9_]
\\W   - Не буква/цифра/подчёркивание
\\s   - Пробельный символ
\\S   - Не пробельный символ
[ ]  - Диапазон или набор символов
( )  - Группа символов
|    - Логическое ИЛИ

Квантификаторы:
*     - 0 или более повторений
+     - 1 или более повторений
?     - 0 или 1 повторение
{n}   - Ровно n повторений
{n,}  - n или более повторений
{n,m} - От n до m повторений

Специальные символы:
\\    - Экранирование специальных символов
\\t   - Табуляция
\\n   - Новая строка
\\r   - Возврат каретки

Примеры:
^\\d+$       - Только цифры
^[а-яё]+$    - Только русские буквы
\\b\\w{3}\\b  - Слова из 3 букв
^\\d{4}-\\d{2}-\\d{2}$ - Дата в формате ГГГГ-ММ-ДД"""

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
            compare_text = filter_text.lower() if not case_sensitive else filter_text
            compare_strings = [s.lower() for s in self.strings] if not case_sensitive else self.strings

            if self.exact_match_var.get():
                self.filtered_strings = [s for s, cs in zip(self.strings, compare_strings) if compare_text == cs]
            else:
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
            self.update_list()
            self.entry.focus()

def show_window() -> None:
    """Показывает окно приложения"""
    app.previous_window = gw.getActiveWindow()
    x, y = pyautogui.position()
    root.geometry(f"+{x}+{y}")
    root.deiconify()
    root.attributes("-topmost", True)
    root.lift()
    root.focus_force()
    app.entry.focus()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = StringListApp(root)
    keyboard.add_hotkey("ctrl+alt+s", show_window)
    root.mainloop()