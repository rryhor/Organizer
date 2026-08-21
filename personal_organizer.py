# Персональный органайзер - скелет приложения на Python + Tkinter (ttk)
# Часть 1: Базовая структура интерфейса, классы-обёртки для полей ввода, модель данных

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import json
import os

# Попытка импорта tkcalendar (может отсутствовать в стандартной установке)
try:
    from tkcalendar import Calendar
except ImportError:
    Calendar = None


class EnhancedEntry(ttk.Entry):
    """
    Класс-обёртка над ttk.Entry с глобальной привязкой горячих клавиш:
    Ctrl+C - копировать, Ctrl+V - вставить, Ctrl+X - вырезать, Ctrl+A - выделить всё.
    Работает глобально во всех полях этого типа в приложении.
    """
    
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        # Привязываем горячие клавиши к виджету
        self.bind('<Control-c>', self._copy)
        self.bind('<Control-v>', self._paste)
        self.bind('<Control-x>', self._cut)
        self.bind('<Control-a>', self._select_all)
    
    def _copy(self, event=None):
        """Копирует выделенный текст в буфер обмена."""
        try:
            self.clipboard_clear()
            self.clipboard_append(self.selection_get())
        except tk.TclError:
            pass  # Нет выделенного текста
        return 'break'
    
    def _paste(self, event=None):
        """Вставляет текст из буфера обмена."""
        try:
            text = self.clipboard_get()
            self.insert(tk.INSERT, text)
        except tk.TclError:
            pass  # Буфер обмена пуст или недоступен
        return 'break'
    
    def _cut(self, event=None):
        """Вырезает выделенный текст (копирует и удаляет)."""
        try:
            text = self.selection_get()
            self.clipboard_clear()
            self.clipboard_append(text)
            self.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass  # Нет выделенного текста
        return 'break'
    
    def _select_all(self, event=None):
        """Выделяет весь текст в поле."""
        self.select_range(0, tk.END)
        self.icursor(tk.END)
        return 'break'


class EnhancedText(tk.Text):
    """
    Класс-обёртка над tk.Text с глобальной привязкой горячих клавиш:
    Ctrl+C - копировать, Ctrl+V - вставить, Ctrl+X - вырезать, Ctrl+A - выделить всё.
    Работает глобально во всех текстовых полях этого типа в приложении.
    """
    
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        # Привязываем горячие клавиши к виджету
        self.bind('<Control-c>', self._copy)
        self.bind('<Control-v>', self._paste)
        self.bind('<Control-x>', self._cut)
        self.bind('<Control-a>', self._select_all)
    
    def _copy(self, event=None):
        """Копирует выделенный текст в буфер обмена."""
        try:
            self.clipboard_clear()
            self.clipboard_append(self.selection_get())
        except tk.TclError:
            pass  # Нет выделенного текста
        return 'break'
    
    def _paste(self, event=None):
        """Вставляет текст из буфера обмена."""
        try:
            text = self.clipboard_get()
            self.insert(tk.INSERT, text)
        except tk.TclError:
            pass  # Буфер обмена пуст или недоступен
        return 'break'
    
    def _cut(self, event=None):
        """Вырезает выделенный текст (копирует и удаляет)."""
        try:
            text = self.selection_get()
            self.clipboard_clear()
            self.clipboard_append(text)
            self.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass  # Нет выделенного текста
        return 'break'
    
    def _select_all(self, event=None):
        """Выделяет весь текст в поле."""
        self.tag_add(tk.SEL, '1.0', tk.END)
        self.mark_set(tk.INSERT, '1.0')
        self.see(tk.INSERT)
        return 'break'


class Task:
    """
    Класс модели задачи со всеми необходимыми полями.
    Используется для хранения и сериализации данных о задачах.
    """
    
    def __init__(self, id=None, title="", task_type="Обычная", due_date=None, 
                 description="", completed=False, notified=False, 
                 reminder_minutes=0, subtasks=None):
        """
        Инициализация задачи с параметрами по умолчанию.
        
        Args:
            id: Уникальный идентификатор задачи (int)
            title: Заголовок задачи (str)
            task_type: Тип задачи (str) - "Обычная", "Встреча", "Звонок" и т.д.
            due_date: Дата выполнения (datetime или str в формате YYYY-MM-DD)
            description: Подробное описание задачи (str)
            completed: Флаг выполнения (bool)
            notified: Флаг уведомления (bool)
            reminder_minutes: Время напоминания в минутах до события (int)
            subtasks: Список подзадач (list)
        """
        self.id = id if id is not None else int(datetime.now().timestamp())
        self.title = title
        self.task_type = task_type
        # Обработка даты: может быть строкой или datetime объектом
        if isinstance(due_date, str) and due_date:
            try:
                self.due_date = datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                self.due_date = None
        elif isinstance(due_date, datetime):
            self.due_date = due_date
        else:
            self.due_date = None
        self.description = description
        self.completed = completed
        self.notified = notified
        self.reminder_minutes = reminder_minutes
        self.subtasks = subtasks if subtasks is not None else []
    
    def to_dict(self):
        """
        Преобразует объект Task в словарь для JSON-сериализации.
        
        Returns:
            dict: Словарь с данными задачи
        """
        return {
            'id': self.id,
            'title': self.title,
            'task_type': self.task_type,
            'due_date': self.due_date.strftime("%Y-%m-%d") if self.due_date else None,
            'description': self.description,
            'completed': self.completed,
            'notified': self.notified,
            'reminder_minutes': self.reminder_minutes,
            'subtasks': self.subtasks
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Создаёт объект Task из словаря (при загрузке из JSON).
        
        Args:
            data: dict с данными задачи
            
        Returns:
            Task: Новый объект задачи
        """
        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            task_type=data.get('task_type', 'Обычная'),
            due_date=data.get('due_date'),
            description=data.get('description', ''),
            completed=data.get('completed', False),
            notified=data.get('notified', False),
            reminder_minutes=data.get('reminder_minutes', 0),
            subtasks=data.get('subtasks', [])
        )
    
    def get_status_group(self):
        """
        Определяет группу задачи для отображения в дереве.
        
        Returns:
            str: Название группы ("Сегодня", "Скоро", "Позже", "Просрочено", "Выполнено")
        """
        if self.completed:
            return "Выполнено"
        
        if self.due_date is None:
            return "Позже"
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        due = self.due_date.replace(hour=0, minute=0, second=0, microsecond=0) if isinstance(self.due_date, datetime) else datetime.strptime(self.due_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        
        if due < today:
            return "Просрочено"
        elif due == today:
            return "Сегодня"
        elif due <= today + timedelta(days=7):
            return "Скоро"
        else:
            return "Позже"


class AddTaskDialog:
    """
    Модальный диалог для создания и редактирования задач.
    Окно 500x600 с полями: тип задачи, название, описание, дата, время, напоминание.
    Поддерживает режим создания новой задачи и режим редактирования существующей.
    Все поля Entry/Text используют EnhancedEntry/EnhancedText для поддержки Ctrl+C/V/X/A.
    """
    
    def __init__(self, parent, task=None, on_save=None):
        """
        Инициализация диалога создания/редактирования задачи.
        
        Args:
            parent: Родительское окно (для модальности)
            task: Объект Task для редактирования (None для создания новой)
            on_save: Callback-функция, вызываемая при успешном сохранении
        """
        self.parent = parent
        self.task = task  # Задача для редактирования или None
        self.on_save = on_save  # Функция обратного вызова после сохранения
        self.result = None  # Результат диалога (сохранённая задача или None)
        
        # Создание модального окна
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавление задачи" if task is None else "Редактирование задачи")
        self.dialog.geometry("500x600")
        self.dialog.minsize(450, 550)
        self.dialog.transient(parent)  # Сделать окном верхнего уровня относительно parent
        self.dialog.grab_set()  # Модальность - перехват всех событий
        
        # Центрирование окна относительно родителя
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 600) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Переменная для хранения результата
        self.saved = False
        
        # Создание интерфейса диалога
        self._create_ui()
        
        # Если передана задача для редактирования - заполнить поля
        if self.task is not None:
            self._fill_from_task()
        
        # Привязка клавиши Enter для сохранения
        self.dialog.bind('<Return>', lambda e: self._on_save())
        # Привязка Escape для отмены
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
    
    def _create_ui(self):
        """
        Создание интерфейса диалога.
        Включает все поля ввода, календарь, spinbox времени и напоминания, кнопки.
        """
        # Основной фрейм с отступами
        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === Поле "Тип задачи" ===
        type_frame = ttk.Frame(main_frame)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(type_frame, text="Тип задачи:", width=15, anchor=tk.E).pack(side=tk.LEFT)
        self.type_combo = ttk.Combobox(type_frame, values=[
            "Встреча", "Мероприятие", "Документы", "Срок сдачи", "Другое"
        ], state="readonly", width=30)
        self.type_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.type_combo.set("Другое")  # Значение по умолчанию
        
        # === Поле "Название" (EnhancedEntry) ===
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(title_frame, text="Название:", width=15, anchor=tk.E).pack(side=tk.LEFT)
        self.title_entry = EnhancedEntry(title_frame, width=40)
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # === Поле "Описание" (EnhancedText, 4 строки) ===
        desc_label = ttk.Label(main_frame, text="Описание:")
        desc_label.pack(anchor=tk.W, pady=(5, 0))
        self.desc_text = EnhancedText(main_frame, height=4, wrap=tk.WORD)
        self.desc_text.pack(fill=tk.X, pady=(0, 10))
        # Добавляем скроллбар для текста
        desc_scrollbar = ttk.Scrollbar(self.desc_text, orient=tk.VERTICAL, command=self.desc_text.yview)
        desc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.desc_text.configure(yscrollcommand=desc_scrollbar.set)
        
        # === Календарь (tkcalendar.Calendar) ===
        cal_label = ttk.Label(main_frame, text="Дата выполнения:")
        cal_label.pack(anchor=tk.W, pady=(5, 0))
        
        if Calendar is not None:
            # Используем tkcalendar.Calendar
            self.calendar = Calendar(main_frame, selectmode='day', 
                                     date_pattern='yyyy-mm-dd', locale='ru_RU')
            self.calendar.pack(fill=tk.X, pady=(0, 10))
            # Установка текущей даты по умолчанию
            self.calendar.selection_clear()
            today = datetime.now()
            self.calendar.select_date(today)
        else:
            # Fallback: поле ввода даты вручную
            self.date_entry = EnhancedEntry(main_frame, width=20)
            self.date_entry.pack(pady=(0, 10))
            self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
            ttk.Label(main_frame, text="(в формате ГГГГ-ММ-ДД)", foreground='gray').pack(anchor=tk.W)
        
        # === Spinbox часов (0-23) и минут (0-59) ===
        time_frame = ttk.Frame(main_frame)
        time_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(time_frame, text="Время:").pack(side=tk.LEFT)
        
        # Часы
        ttk.Label(time_frame, text="Часы:").pack(side=tk.LEFT, padx=(15, 5))
        self.hour_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, width=5, 
                                        format="%02.0f", command=self._validate_time)
        self.hour_spinbox.pack(side=tk.LEFT)
        self.hour_spinbox.set(12)  # Полдень по умолчанию
        
        # Минуты
        ttk.Label(time_frame, text="Минуты:").pack(side=tk.LEFT, padx=(10, 5))
        self.minute_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, width=5, 
                                          format="%02.0f", command=self._validate_time)
        self.minute_spinbox.pack(side=tk.LEFT)
        self.minute_spinbox.set(0)
        
        # === Поле "Напомнить за (минут)" (Spinbox, 5-1440, шаг 5) ===
        reminder_frame = ttk.Frame(main_frame)
        reminder_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(reminder_frame, text="Напомнить за:", width=15, anchor=tk.E).pack(side=tk.LEFT)
        self.reminder_spinbox = ttk.Spinbox(reminder_frame, from_=5, to=1440, width=10, 
                                            increment=5, command=self._validate_reminder)
        self.reminder_spinbox.pack(side=tk.LEFT, padx=5)
        self.reminder_spinbox.set(15)  # 15 минут по умолчанию
        ttk.Label(reminder_frame, text="минут до события").pack(side=tk.LEFT)
        
        # === Разделитель ===
        separator = ttk.Separator(main_frame, orient=tk.HORIZONTAL)
        separator.pack(fill=tk.X, pady=15)
        
        # === Кнопки "Сохранить" / "Отмена" ===
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Кнопка Сохранить
        self.save_btn = ttk.Button(btn_frame, text="Сохранить", command=self._on_save)
        self.save_btn.pack(side=tk.RIGHT, padx=5)
        
        # Кнопка Отмена
        cancel_btn = ttk.Button(btn_frame, text="Отмена", command=self.dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
    
    def _fill_from_task(self):
        """
        Заполнение полей диалога данными из объекта Task (режим редактирования).
        Извлекает все данные задачи и устанавливает их в соответствующие поля.
        """
        if self.task is None:
            return
        
        # Тип задачи
        if self.task.task_type in ["Встреча", "Мероприятие", "Документы", "Срок сдачи", "Другое"]:
            self.type_combo.set(self.task.task_type)
        else:
            self.type_combo.set("Другое")
        
        # Название
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, self.task.title)
        
        # Описание
        self.desc_text.delete('1.0', tk.END)
        self.desc_text.insert('1.0', self.task.description)
        
        # Дата и время
        if self.task.due_date:
            due_dt = self.task.due_date if isinstance(self.task.due_date, datetime) else \
                     datetime.strptime(self.task.due_date, "%Y-%m-%d")
            
            if Calendar is not None:
                self.calendar.select_date(due_dt)
            else:
                self.date_entry.delete(0, tk.END)
                self.date_entry.insert(0, due_dt.strftime("%Y-%m-%d"))
            
            # Время
            self.hour_spinbox.set(due_dt.hour)
            self.minute_spinbox.set(due_dt.minute)
        
        # Напоминание
        if self.task.reminder_minutes and self.task.reminder_minutes >= 5:
            self.reminder_spinbox.set(self.task.reminder_minutes)
        else:
            self.reminder_spinbox.set(15)
    
    def _validate_time(self):
        """
        Валидация введённого времени.
        Проверяет корректность значений часов (0-23) и минут (0-59).
        """
        try:
            hour = int(self.hour_spinbox.get())
            minute = int(self.minute_spinbox.get())
            if hour < 0 or hour > 23:
                self.hour_spinbox.set(12)
            if minute < 0 or minute > 59:
                self.minute_spinbox.set(0)
        except ValueError:
            self.hour_spinbox.set(12)
            self.minute_spinbox.set(0)
    
    def _validate_reminder(self):
        """
        Валидация значения напоминания.
        Проверяет, что значение в диапазоне 5-1440 минут.
        """
        try:
            reminder = int(self.reminder_spinbox.get())
            if reminder < 5:
                self.reminder_spinbox.set(5)
            elif reminder > 1440:
                self.reminder_spinbox.set(1440)
        except ValueError:
            self.reminder_spinbox.set(15)
    
    def _on_save(self):
        """
        Обработчик нажатия кнопки "Сохранить".
        Выполняет валидацию полей, создаёт/обновляет объект Task и закрывает диалог.
        """
        # Валидация: название обязательно
        title = self.title_entry.get().strip()
        if not title:
            # Показываем сообщение об ошибке
            error_dialog = tk.Toplevel(self.dialog)
            error_dialog.title("Ошибка")
            error_dialog.geometry("300x100")
            error_dialog.transient(self.dialog)
            error_dialog.grab_set()
            ttk.Label(error_dialog, text="Название задачи обязательно!", 
                     foreground='red').pack(pady=20)
            ttk.Button(error_dialog, text="OK", command=error_dialog.destroy).pack()
            # Центрирование
            error_dialog.update_idletasks()
            x = self.dialog.winfo_x() + (500 - 300) // 2
            y = self.dialog.winfo_y() + (600 - 100) // 2
            error_dialog.geometry(f"+{x}+{y}")
            return
        
        # Валидация даты
        try:
            if Calendar is not None:
                date_str = self.calendar.get_date()
                due_date = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                date_str = self.date_entry.get().strip()
                due_date = datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            # Показываем сообщение об ошибке
            error_dialog = tk.Toplevel(self.dialog)
            error_dialog.title("Ошибка")
            error_dialog.geometry("300x100")
            error_dialog.transient(self.dialog)
            error_dialog.grab_set()
            ttk.Label(error_dialog, text="Некорректная дата!", foreground='red').pack(pady=20)
            ttk.Button(error_dialog, text="OK", command=error_dialog.destroy).pack()
            error_dialog.update_idletasks()
            x = self.dialog.winfo_x() + (500 - 300) // 2
            y = self.dialog.winfo_y() + (600 - 100) // 2
            error_dialog.geometry(f"+{x}+{y}")
            return
        
        # Сбор времени
        try:
            hour = int(self.hour_spinbox.get())
            minute = int(self.minute_spinbox.get())
            due_datetime = due_date.replace(hour=hour, minute=minute)
        except ValueError:
            due_datetime = due_date
        
        # Сбор данных
        task_type = self.type_combo.get()
        description = self.desc_text.get('1.0', tk.END).strip()
        reminder_minutes = int(self.reminder_spinbox.get())
        
        # Создание или обновление объекта Task
        if self.task is None:
            # Создание новой задачи
            new_task = Task(
                id=int(datetime.now().timestamp()),
                title=title,
                task_type=task_type,
                due_date=due_datetime,
                description=description,
                completed=False,
                notified=False,
                reminder_minutes=reminder_minutes,
                subtasks=[]
            )
            self.result = new_task
        else:
            # Обновление существующей задачи
            self.task.title = title
            self.task.task_type = task_type
            self.task.due_date = due_datetime
            self.task.description = description
            self.task.reminder_minutes = reminder_minutes
            self.result = self.task
        
        # Помечаем как сохранённое и закрываем
        self.saved = True
        if self.on_save:
            self.on_save(self.result)
        self.dialog.destroy()
    
    def wait_for_result(self):
        """
        Ожидание закрытия диалога и возврат результата.
        Блокирует выполнение до закрытия окна.
        
        Returns:
            Task или None: Сохранённая задача или None если отменено
        """
        self.dialog.wait_window()
        return self.result


class PersonalOrganizerApp:
    """
    Главный класс приложения персонального органайзера.
    Содержит всю логику интерфейса, управление данными и обработчики событий.
    """
    
    def __init__(self, root):
        """
        Инициализация приложения: настройка стилей, создание интерфейса, загрузка данных.
        
        Args:
            root: Главное окно Tkinter
        """
        self.root = root
        self.root.title("Персональный органайзер")
        self.root.geometry("1000x650")
        self.root.minsize(800, 600)
        
        # Хранилище задач
        self.tasks = {}
        self.current_task_id = None
        
        # Настройка стиля приложения
        self._setup_styles()
        
        # Создание основного интерфейса
        self._create_ui()
        
        # Загрузка данных из файла
        self._load_data()
        
        # Обновление дерева задач
        self._refresh_task_tree()
    
    def _setup_styles(self):
        """
        Настройка ttk.Style: светлая тема, аккуратные отступы, шрифт Segoe UI 10pt.
        Создает единый визуальный стиль для всех виджетов приложения.
        """
        style = ttk.Style()
        
        # Используем доступную тему как основу
        available_themes = style.theme_names()
        if 'vista' in available_themes:
            style.theme_use('vista')
        elif 'clam' in available_themes:
            style.theme_use('clam')
        
        # Базовый шрифт для приложения
        default_font = ('Segoe UI', 10)
        
        # Настройка базовых стилей
        style.configure('.', font=default_font)
        style.configure('TLabel', font=default_font, padding=2)
        style.configure('TButton', font=default_font, padding=5)
        style.configure('TEntry', font=default_font, padding=5)
        style.configure('Treeview', font=default_font, rowheight=25)
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))
        
        # Настройка цветов для светлой темы
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0')
        
        # Стили для панелей
        style.configure('Toolbar.TFrame', background='#e0e0e0')
        style.configure('LeftPanel.TFrame', background='#f5f5f5')
        style.configure('RightPanel.TFrame', background='#ffffff')
    
    def _create_ui(self):
        """
        Создание основного интерфейса приложения.
        Включает: верхнюю панель, левую панель с деревом задач, правую панель с деталями.
        """
        # Основной контейнер
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Создание верхней панели (toolbar)
        self._create_toolbar()
        
        # Создание центральной области с двумя панелями
        self._create_central_area()
    
    def _create_toolbar(self):
        """
        Создание верхней панели с полем поиска и кнопками-фильтрами.
        Панель содержит элементы управления для фильтрации и поиска задач.
        """
        # Контейнер toolbar
        self.toolbar_frame = ttk.Frame(self.main_frame, style='Toolbar.TFrame')
        self.toolbar_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Левая часть toolbar - поиск
        search_frame = ttk.Frame(self.toolbar_frame, style='Toolbar.TFrame')
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Метка и поле поиска
        ttk.Label(search_frame, text="Поиск:", style='Toolbar.TFrame').pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = EnhancedEntry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Кнопка очистки поиска
        self.clear_search_btn = ttk.Button(search_frame, text="✕", width=3, command=self._clear_search)
        self.clear_search_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Правая часть toolbar - кнопки фильтров
        filter_frame = ttk.Frame(self.toolbar_frame, style='Toolbar.TFrame')
        filter_frame.pack(side=tk.RIGHT)
        
        # Кнопки фильтров по статусам
        self.filter_all_btn = ttk.Button(filter_frame, text="Все", command=lambda: self._filter_tasks('all'))
        self.filter_all_btn.pack(side=tk.LEFT, padx=2)
        
        self.filter_today_btn = ttk.Button(filter_frame, text="Сегодня", command=lambda: self._filter_tasks('Сегодня'))
        self.filter_today_btn.pack(side=tk.LEFT, padx=2)
        
        self.filter_soon_btn = ttk.Button(filter_frame, text="Скоро", command=lambda: self._filter_tasks('Скоро'))
        self.filter_soon_btn.pack(side=tk.LEFT, padx=2)
        
        self.filter_later_btn = ttk.Button(filter_frame, text="Позже", command=lambda: self._filter_tasks('Позже'))
        self.filter_later_btn.pack(side=tk.LEFT, padx=2)
        
        self.filter_overdue_btn = ttk.Button(filter_frame, text="Просрочено", command=lambda: self._filter_tasks('Просрочено'))
        self.filter_overdue_btn.pack(side=tk.LEFT, padx=2)
        
        self.filter_completed_btn = ttk.Button(filter_frame, text="Выполнено", command=lambda: self._filter_tasks('Выполнено'))
        self.filter_completed_btn.pack(side=tk.LEFT, padx=2)
        
        # Текущий фильтр
        self.current_filter = 'all'
    
    def _create_central_area(self):
        """
        Создание центральной области с левой и правой панелями.
        Левая панель (250px) - Treeview со списком задач.
        Правая панель - область деталей выбранной задачи.
        """
        # Контейнер для двух панелей
        central_frame = ttk.Frame(self.main_frame)
        central_frame.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель со списком задач
        self._create_left_panel(central_frame)
        
        # Разделитель между панелями
        separator = ttk.Separator(central_frame, orient=tk.VERTICAL)
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Правая панель с деталями задачи
        self._create_right_panel(central_frame)
    
    def _create_left_panel(self, parent):
        """
        Создание левой панели с Treeview для отображения списка задач.
        Задачи группируются по статусам: Сегодня, Скоро, Позже, Просрочено, Выполнено.
        
        Args:
            parent: Родительский контейнер
        """
        # Фрейм левой панели
        left_frame = ttk.Frame(parent, width=250)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        left_frame.pack_propagate(False)  # Фиксируем ширину
        
        # Заголовок
        ttk.Label(left_frame, text="Задачи", font=('Segoe UI', 12, 'bold')).pack(pady=5)
        
        # Контейнер для Treeview с прокруткой
        tree_container = ttk.Frame(left_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar для дерева
        tree_scrollbar = ttk.Scrollbar(tree_container)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview для отображения задач с группировкой
        columns = ('title', 'type', 'due_date')
        self.task_tree = ttk.Treeview(tree_container, columns=columns, show='tree headings', 
                                       yscrollcommand=tree_scrollbar.set)
        self.task_tree.pack(fill=tk.BOTH, expand=True)
        
        # Настройка scrollbar
        tree_scrollbar.config(command=self.task_tree.yview)
        
        # Настройка колонок
        self.task_tree.heading('#0', text='Название', anchor=tk.W)
        self.task_tree.heading('title', text='Задача', anchor=tk.W)
        self.task_tree.heading('type', text='Тип', anchor=tk.W)
        self.task_tree.heading('due_date', text='Дата', anchor=tk.W)
        
        self.task_tree.column('#0', width=200, minwidth=150)
        self.task_tree.column('title', width=1, minwidth=0)  # Скрытая колонка
        self.task_tree.column('type', width=60, minwidth=50)
        self.task_tree.column('due_date', width=70, minwidth=60)
        
        # Привязка события выбора задачи
        self.task_tree.bind('<<TreeviewSelect>>', self._on_task_select)
        self.task_tree.bind('<Double-1>', self._on_task_double_click)
        
        # Кнопки управления задачами
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.add_task_btn = ttk.Button(btn_frame, text="+ Добавить", command=self._add_task)
        self.add_task_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.edit_task_btn = ttk.Button(btn_frame, text="✎ Изменить", command=self._edit_task)
        self.edit_task_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.delete_task_btn = ttk.Button(btn_frame, text="🗑 Удалить", command=self._delete_task)
        self.delete_task_btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
    
    def _create_right_panel(self, parent):
        """
        Создание правой панели для отображения и редактирования деталей задачи.
        Содержит поля: заголовок, тип, дата, описание, подзадачи, напоминание.
        
        Args:
            parent: Родительский контейнер
        """
        # Фрейм правой панели
        right_frame = ttk.Frame(parent, style='RightPanel.TFrame')
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Заголовок панели
        header_frame = ttk.Frame(right_frame)
        header_frame.pack(fill=tk.X, pady=5)
        
        self.detail_title_label = ttk.Label(header_frame, text="Детали задачи", 
                                            font=('Segoe UI', 14, 'bold'))
        self.detail_title_label.pack(side=tk.LEFT)
        
        # Кнопка завершения задачи
        self.complete_btn = ttk.Button(header_frame, text="✓ Выполнено", 
                                       command=self._toggle_complete, state=tk.DISABLED)
        self.complete_btn.pack(side=tk.RIGHT)
        
        # Контейнер для полей детали с прокруткой
        details_container = ttk.Frame(right_frame)
        details_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar для правой панели
        details_scrollbar = ttk.Scrollbar(details_container)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas для прокручиваемой области
        self.details_canvas = tk.Canvas(details_container, yscrollcommand=details_scrollbar.set,
                                        highlightthickness=0)
        self.details_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scrollbar.config(command=self.details_canvas.yview)
        
        # Фрейм внутри canvas для размещения элементов
        self.details_inner_frame = ttk.Frame(self.details_canvas)
        self.details_canvas_window = self.details_canvas.create_window((0, 0), window=self.details_inner_frame, 
                                                                        anchor=tk.NW)
        
        # Привязка изменения размера для обновления области прокрутки
        self.details_inner_frame.bind('<Configure>', self._on_details_frame_configure)
        self.details_canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Поля деталей задачи
        self._create_detail_fields()
        
        # Изначально скрываем детали (нет выбранной задачи)
        self._hide_details()
    
    def _create_detail_fields(self):
        """
        Создание полей для отображения и редактирования деталей задачи.
        Использует EnhancedEntry и EnhancedText для поддержки горячих клавиш.
        """
        # Поле заголовка
        title_frame = ttk.Frame(self.details_inner_frame)
        title_frame.pack(fill=tk.X, pady=5)
        ttk.Label(title_frame, text="Заголовок:", width=15, anchor=tk.E).pack(side=tk.LEFT)
        self.title_entry = EnhancedEntry(title_frame, width=50)
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.title_entry.bind('<KeyRelease>', self._on_field_change)
        
        # Поле типа задачи
        type_frame = ttk.Frame(self.details_inner_frame)
        type_frame.pack(fill=tk.X, pady=5)
        ttk.Label(type_frame, text="Тип:", width=15, anchor=tk.E).pack(side=tk.LEFT)
        self.type_combo = ttk.Combobox(type_frame, values=["Обычная", "Встреча", "Звонок", 
                                                            "Событие", "Дедлайн"], width=47)
        self.type_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.type_combo.bind('<<ComboboxSelected>>', self._on_field_change)
        
        # Поле даты выполнения
        date_frame = ttk.Frame(self.details_inner_frame)
        date_frame.pack(fill=tk.X, pady=5)
        ttk.Label(date_frame, text="Дата выполнения:", width=15, anchor=tk.E).pack(side=tk.LEFT)
        self.date_entry = EnhancedEntry(date_frame, width=20)
        self.date_entry.pack(side=tk.LEFT, padx=5)
        self.date_entry.bind('<KeyRelease>', self._on_field_change)
        
        # Кнопка выбора даты (если доступен tkcalendar)
        if Calendar is not None:
            self.calendar_btn = ttk.Button(date_frame, text="📅", command=self._show_calendar)
            self.calendar_btn.pack(side=tk.LEFT, padx=2)
        else:
            ttk.Label(date_frame, text="(в формате ГГГГ-ММ-ДД)").pack(side=tk.LEFT, padx=5)
        
        # Поле времени напоминания
        reminder_frame = ttk.Frame(self.details_inner_frame)
        reminder_frame.pack(fill=tk.X, pady=5)
        ttk.Label(reminder_frame, text="Напоминание:", width=15, anchor=tk.E).pack(side=tk.LEFT)
        self.reminder_spinbox = ttk.Spinbox(reminder_frame, from_=0, to=1440, width=10, 
                                            increment=15, command=self._on_field_change)
        self.reminder_spinbox.pack(side=tk.LEFT, padx=5)
        ttk.Label(reminder_frame, text="минут до события").pack(side=tk.LEFT)
        self.reminder_spinbox.bind('<KeyRelease>', self._on_field_change)
        
        # Поле описания
        desc_label = ttk.Label(self.details_inner_frame, text="Описание:")
        desc_label.pack(anchor=tk.W, pady=(10, 0))
        self.description_text = EnhancedText(self.details_inner_frame, height=8, wrap=tk.WORD)
        self.description_text.pack(fill=tk.X, pady=5)
        self.description_text.bind('<KeyRelease>', self._on_field_change)
        
        # Подзадачи
        subtasks_label = ttk.Label(self.details_inner_frame, text="Подзадачи:")
        subtasks_label.pack(anchor=tk.W, pady=(10, 0))
        
        subtasks_container = ttk.Frame(self.details_inner_frame)
        subtasks_container.pack(fill=tk.X, pady=5)
        
        # Список подзадач
        self.subtasks_listbox = tk.Listbox(subtasks_container, height=5, selectmode=tk.EXTENDED)
        self.subtasks_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Кнопки управления подзадачами
        subtasks_btn_frame = ttk.Frame(subtasks_container)
        subtasks_btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(subtasks_btn_frame, text="+", width=3, command=self._add_subtask).pack(pady=1)
        ttk.Button(subtasks_btn_frame, text="-", width=3, command=self._remove_subtask).pack(pady=1)
        ttk.Button(subtasks_btn_frame, text="✓", width=3, command=self._complete_subtask).pack(pady=1)
        
        # Статус создания/изменения
        self.status_label = ttk.Label(self.details_inner_frame, text="", foreground='gray')
        self.status_label.pack(anchor=tk.W, pady=5)
    
    def _refresh_task_tree(self):
        """
        Обновление дерева задач на основе текущего фильтра.
        Очищает дерево и заново заполняет его задачами из хранилища.
        """
        pass  # Заглушка для части 1
    
    def _filter_tasks(self, filter_type):
        """
        Фильтрация задач по типу и обновление дерева.
        
        Args:
            filter_type: Тип фильтра ('all', 'Сегодня', 'Скоро', 'Позже', 'Просрочено', 'Выполнено')
        """
        pass  # Заглушка для части 1
    
    def _clear_search(self):
        """Очистка поля поиска и сброс фильтрации."""
        pass  # Заглушка для части 1
    
    def _on_task_select(self, event):
        """
        Обработчик выбора задачи в дереве.
        Загружает детали выбранной задачи в правую панель.
        
        Args:
            event: Событие выбора
        """
        pass  # Заглушка для части 1
    
    def _on_task_double_click(self, event):
        """
        Обработчик двойного клика по задаче.
        Открывает диалог редактирования (будет реализовано в части 2).
        
        Args:
            event: Событие клика
        """
        pass  # Заглушка для части 1
    
    def _add_task(self):
        """
        Создание новой задачи через диалог AddTaskDialog.
        Открывает модальное окно для ввода данных задачи.
        После сохранения добавляет задачу в хранилище и обновляет дерево.
        """
        def on_save(task):
            """Callback после успешного сохранения задачи."""
            if task:
                self.tasks[task.id] = task
                self._refresh_task_tree()
                self._save_data()
        
        # Создаём и показываем диалог
        dialog = AddTaskDialog(self.root, task=None, on_save=on_save)
        dialog.wait_for_result()
    
    def _edit_task(self):
        """
        Редактирование выбранной задачи через диалог AddTaskDialog.
        Открывает модальное окно с заполненными полями текущей задачи.
        После сохранения обновляет данные и дерево задач.
        """
        # Проверяем, есть ли выбранная задача
        if self.current_task_id is None or self.current_task_id not in self.tasks:
            return
        
        task = self.tasks[self.current_task_id]
        
        def on_save(task):
            """Callback после успешного сохранения задачи."""
            if task:
                self.tasks[task.id] = task
                self._refresh_task_tree()
                self._show_details()  # Обновить отображение деталей
                self._save_data()
        
        # Создаём и показываем диалог с задачей для редактирования
        dialog = AddTaskDialog(self.root, task=task, on_save=on_save)
        dialog.wait_for_result()
    
    def _delete_task(self):
        """Удаление выбранной задачи."""
        pass  # Заглушка для части 1
    
    def _toggle_complete(self):
        """Переключение статуса выполнения текущей задачи."""
        pass  # Заглушка для части 1
    
    def _on_field_change(self, event=None):
        """
        Обработчик изменения любого поля детали задачи.
        Отмечает задачу как несохранённую.
        
        Args:
            event: Событие изменения
        """
        pass  # Заглушка для части 1
    
    def _show_calendar(self):
        """Показать календарь для выбора даты (если tkcalendar доступен)."""
        pass  # Заглушка для части 1
    
    def _hide_details(self):
        """Скрытие панели деталей (когда задача не выбрана)."""
        pass  # Заглушка для части 1
    
    def _show_details(self):
        """Показ панели деталей с данными текущей задачи."""
        pass  # Заглушка для части 1
    
    def _save_current_task(self):
        """Сохранение изменений текущей задачи."""
        pass  # Заглушка для части 1
    
    def _add_subtask(self):
        """Добавление подзадачи к текущей задаче."""
        pass  # Заглушка для части 1
    
    def _remove_subtask(self):
        """Удаление выбранной подзадачи."""
        pass  # Заглушка для части 1
    
    def _complete_subtask(self):
        """Отметка подзадачи как выполненной."""
        pass  # Заглушка для части 1
    
    def _on_details_frame_configure(self, event):
        """Обновление области прокрутки при изменении размера фрейма деталей."""
        self.details_canvas.configure(scrollregion=self.details_canvas.bbox('all'))
    
    def _on_canvas_configure(self, event):
        """Подстройка ширины внутреннего фрейма под canvas."""
        self.details_canvas.itemconfig(self.details_canvas_window, width=event.width)
    
    def _load_data(self):
        """
        Загрузка данных задач из JSON-файла organizer_data.json.
        Если файл не существует, создаётся пустое хранилище.
        """
        pass  # Заглушка для части 1
    
    def _save_data(self):
        """
        Сохранение всех задач в JSON-файл organizer_data.json.
        Вызывается при закрытии приложения и после значимых изменений.
        """
        pass  # Заглушка для части 1
    
    def _on_close(self):
        """
        Обработчик закрытия окна приложения.
        Сохраняет данные перед выходом.
        """
        self._save_data()
        self.root.destroy()


def main():
    """
    Точка входа в приложение.
    Создаёт главное окно, инициализирует приложение и запускает mainloop.
    """
    # Создание главного окна
    root = tk.Tk()
    
    # Создание экземпляра приложения
    app = PersonalOrganizerApp(root)
    
    # Привязка обработчика закрытия окна
    root.protocol("WM_DELETE_WINDOW", app._on_close)
    
    # Запуск главного цикла обработки событий
    root.mainloop()


if __name__ == "__main__":
    main()
