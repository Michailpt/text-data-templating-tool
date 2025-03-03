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
import pystray
from pystray import MenuItem as item
from PIL import Image
import threading

global_strings: List[str] = ["Пример строки 1", "Пример строки 2", "Пример строки 3"]

class StringListApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("String List")
        self.root.geometry("400x300")
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.data_file = "strings.json"
        self.settings_file = "settings.json"
        self.strings = self.load_strings()
        self.tray_icon = None  # Инициализируем tray_icon как None заранее
        
        # Определение всех переменных настроек
        self.always_on_top_var = tk.BooleanVar(value=True)
        self.save_size_var = tk.BooleanVar(value=False)
        self.exact_match_var = tk.BooleanVar(value=False)
        self.case_sensitive_var = tk.BooleanVar(value=False)
        self.keep_search_var = tk.BooleanVar(value=False)
        self.regex_pattern_var = tk.BooleanVar(value=False)
        
        # Поле поиска без трассировки пока
        self.filter_var = tk.StringVar()
        
        # Загрузка всех настроек
        self.load_settings()
        
        # Меню
        self.menu_bar = tk.Menu(root)
        
        # Меню Файл
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Выход", command=self.quit_app)
        self.menu_bar.add_cascade(label="Файл", menu=self.file_menu)
        
        # Меню Поиск
        self.search_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.search_menu.add_checkbutton(label="Фраза целиком", variable=self.exact_match_var, command=self.update_list)
        self.search_menu.add_checkbutton(label="Учитывать регистр", variable=self.case_sensitive_var, command=self.update_list)
        self.search_menu.add_checkbutton(label="Сохранять условия поиска", variable=self.keep_search_var, command=self.save_settings)
        self.search_menu.add_separator()
        self.search_menu.add_checkbutton(label="Режим регулярных выражений", variable=self.regex_pattern_var, command=self.update_list)
        self.menu_bar.add_cascade(label="Поиск", menu=self.search_menu)
        
        # Меню Вид
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.view_menu.add_checkbutton(label="Поверх всех окон", variable=self.always_on_top_var, command=self.toggle_always_on_top)
        self.view_menu.add_checkbutton(label="Сохранять размер окна", variable=self.save_size_var, command=self.toggle_save_size)
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

        input_frame = ttk.Frame(root)
        input_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.entry = ttk.Entry(input_frame, textvariable=self.filter_var)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.listbox = tk.Listbox(root)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Теперь, когда listbox создан, можно добавить трассировку
        self.filter_var.trace("w", lambda *args: self.update_list())
        self.update_list()  # Начальное обновление списка

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
        self.root.bind("<Configure>", self.save_window_size)

    def load_strings(self) -> List[str]:
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return global_strings.copy()

    def load_settings(self) -> None:
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                if "size" in settings and settings.get("save_size", False):
                    width = settings["size"]["width"]
                    height = settings["size"]["height"]
                    self.root.geometry(f"{width}x{height}")
                self.always_on_top_var.set(settings.get("always_on_top", True))
                self.save_size_var.set(settings.get("save_size", False))
                self.exact_match_var.set(settings.get("exact_match", False))
                self.case_sensitive_var.set(settings.get("case_sensitive", False))
                self.keep_search_var.set(settings.get("keep_search", False))
                self.regex_pattern_var.set(settings.get("regex_pattern", False))
                if settings.get("keep_search", False):
                    self.filter_var.set(settings.get("search_text", ""))
                self.root.attributes("-topmost", self.always_on_top_var.get())
        except FileNotFoundError:
            pass

    def save_settings(self) -> None:
        settings = {
            "always_on_top": self.always_on_top_var.get(),
            "save_size": self.save_size_var.get(),
            "exact_match": self.exact_match_var.get(),
            "case_sensitive": self.case_sensitive_var.get(),
            "keep_search": self.keep_search_var.get(),
            "regex_pattern": self.regex_pattern_var.get(),
            "search_text": self.filter_var.get() if self.keep_search_var.get() else "",
            "size": {
                "width": self.root.winfo_width(),
                "height": self.root.winfo_height()
            }
        }
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

    def save_strings(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.strings, f, ensure_ascii=False, indent=2)

    def save_window_size(self, event: tk.Event) -> None:
        if self.save_size_var.get():
            self.save_settings()

    def toggle_save_size(self) -> None:
        self.save_settings()

    def toggle_always_on_top(self) -> None:
        self.root.attributes("-topmost", self.always_on_top_var.get())
        self.save_settings()

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
        info_text = ("String List\n\nВерсия 1.1\nАвтор: Ваше имя\nЛицензия: MIT\n\n"
                     "Программа для быстрой вставки\nчасто используемых строковых шаблонов")
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
        filter_text = self.filter_var.get()
        self.save_settings()
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
                self.filtered_strings = [s for s, cs in zip(self.strings, compare_strings) if compare_text in cs]
            else:
                filter_words = compare_text.split()
                self.filtered_strings = [s for s, cs in zip(self.strings, compare_strings) if all(word in cs for word in filter_words)]
        self.listbox.delete(0, tk.END)
        for s in self.filtered_strings:
            self.listbox.insert(tk.END, s)

    def insert_string(self, event: Optional[tk.Event] = None) -> None:
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
        self.save_settings()
        if not self.keep_search_var.get():
            self.filter_var.set("")
            self.update_list()
        self.root.withdraw()  # Скрываем окно в трей

    def add_string(self) -> None:
        new_string = self.filter_var.get().strip()
        if new_string and new_string not in self.strings:
            self.strings.append(new_string)
            self.save_strings()
            self.update_list()
            self.filter_var.set("")
            self.entry.focus()

    def edit_string(self) -> None:
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
        if self.editing_index is not None:
            new_string = self.filter_var.get().strip()
            if new_string and new_string not in self.strings:
                self.strings[self.editing_index] = new_string
                self.save_strings()
            self.cleanup_edit()

    def cancel_edit(self) -> None:
        self.cleanup_edit()

    def cleanup_edit(self) -> None:
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
        selected = self.listbox.curselection()
        if selected:
            selected_string = self.filtered_strings[selected[0]]
            self.strings.remove(selected_string)
            self.save_strings()
            self.update_list()
            self.entry.focus()

    def quit_app(self):
        """Полное завершение приложения"""
        self.save_settings()
        if self.tray_icon:  # Проверяем, существует ли tray_icon перед остановкой
            self.tray_icon.stop()
        self.root.quit()

def show_window(icon=None, item=None) -> None:
    app.previous_window = gw.getActiveWindow()
    x, y = pyautogui.position()
    app.root.geometry(f"+{x}+{y}")
    app.root.deiconify()
    app.root.attributes("-topmost", app.always_on_top_var.get())
    app.root.lift()
    app.root.focus_force()
    app.entry.focus()

def quit_app(icon, item):
    app.quit_app()

def setup_tray(app_instance):
    # Создаём простую иконку (можно заменить на свою)
    image = Image.new('RGB', (64, 64), color=(73, 109, 137))  # Цветная заглушка
    # Если у вас есть своя иконка, раскомментируйте следующую строку и укажите путь:
    # image = Image.open("path/to/your/icon.png")
    
    menu = (item('Показать', show_window), item('Выход', quit_app))
    app_instance.tray_icon = pystray.Icon("string_list", image, "String List", menu)
    app_instance.tray_icon.run()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Скрываем окно при запуске
    app = StringListApp(root)
    
    # Запускаем трей в отдельном потоке, передавая экземпляр app
    tray_thread = threading.Thread(target=setup_tray, args=(app,), daemon=True)
    tray_thread.start()
    
    keyboard.add_hotkey("ctrl+alt+s", show_window)
    root.mainloop()