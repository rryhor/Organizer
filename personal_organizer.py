#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Персональный органайзер-планировщик
Полная реализация согласно спецификации из organizer_interface_schemas.docx и .md
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
from datetime import datetime, timedelta
import subprocess

DATA_FILE = "organizer_data.json"


class TaskOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("ОРГАНАЙЗЕР-ПЛАНИРОВЩИК")
        self.root.geometry("1200x800")
        
        # Данные
        self.tasks = []
        self.templates = []
        self.settings = {
            "language": "Russian",
            "theme": "Light",
            "week_start": "Monday",
            "date_format": "%d.%m.%Y",
            "time_format": "24h",
            "notifications_enabled": True,
            "reminder_before": 30,
            "sound_notifications": True,
            "popup_notifications": True,
            "eisenhower_matrix": True,
            "pomodoro_enabled": False,
            "pomodoro_focus": 25,
            "pomodoro_break": 5
        }
        
        self.load_data()
        self.setup_ui()
        self.refresh_task_tree()
        self.update_status_bar()
        
    def load_data(self):
        """Загрузка данных из JSON файла"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = data.get('tasks', [])
                    self.templates = data.get('templates', self.get_default_templates())
                    self.settings.update(data.get('settings', {}))
            except Exception as e:
                print(f"Ошибка загрузки данных: {e}")
                self.templates = self.get_default_templates()
        else:
            self.templates = self.get_default_templates()
    
    def save_data(self):
        """Сохранение данных в JSON файл"""
        data = {
            'tasks': self.tasks,
            'templates': self.templates,
            'settings': self.settings
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_default_templates(self):
        """Шаблоны по умолчанию"""
        return [
            {"id": 1, "name": "Еженедельный отчет", "category": "Работа", 
             "description": "Подготовка еженедельного отчета",
             "subtasks": [{"title": "Собрать данные", "importance": 4, "urgency": 3},
                         {"title": "Написать отчет", "importance": 5, "urgency": 4},
                         {"title": "Отправить руководству", "importance": 5, "urgency": 5}]},
            {"id": 2, "name": "Запуск проекта", "category": "Проекты",
             "description": "Шаблон для запуска нового проекта",
             "subtasks": [{"title": "Анализ требований", "importance": 5, "urgency": 4},
                         {"title": "Планирование", "importance": 4, "urgency": 3},
                         {"title": "Реализация", "importance": 4, "urgency": 4},
                         {"title": "Тестирование", "importance": 5, "urgency": 4},
                         {"title": "Релиз", "importance": 5, "urgency": 5}]},
            {"id": 3, "name": "Встреча с клиентом", "category": "Работа",
             "description": "Подготовка и проведение встречи",
             "subtasks": [{"title": "Подготовить презентацию", "importance": 4, "urgency": 4},
                         {"title": "Согласовать время", "importance": 3, "urgency": 3},
                         {"title": "Провести встречу", "importance": 5, "urgency": 4},
                         {"title": "Отправить итоги", "importance": 4, "urgency": 3}]},
            {"id": 4, "name": "Ревью кода", "category": "Разработка",
             "description": "Проверка кода коллеги",
             "subtasks": [{"title": "Изучить изменения", "importance": 4, "urgency": 3},
                         {"title": "Найти проблемы", "importance": 5, "urgency": 3},
                         {"title": "Оставить комментарии", "importance": 4, "urgency": 3},
                         {"title": "Проверить исправления", "importance": 4, "urgency": 3}]},
            {"id": 5, "name": "Планирование спринта", "category": "Разработка",
             "description": "Планирование задач на спринт",
             "subtasks": [{"title": "Обзор бэклога", "importance": 4, "urgency": 3},
                         {"title": "Оценка задач", "importance": 4, "urgency": 3},
                         {"title": "Распределение задач", "importance": 5, "urgency": 4},
                         {"title": "Фиксация плана", "importance": 4, "urgency": 4}]},
            {"id": 6, "name": "Обработка почты", "category": "Рутина",
             "description": "Ежедневная обработка электронной почты",
             "subtasks": [{"title": "Просмотреть входящие", "importance": 3, "urgency": 3},
                         {"title": "Ответить на срочные", "importance": 4, "urgency": 4},
                         {"title": "Отсортировать остальные", "importance": 2, "urgency": 2},
                         {"title": "Архивировать", "importance": 2, "urgency": 1}]}
        ]
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Главное меню
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Сохранить", command=self.save_data)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)
        
        task_menu = tk.Menu(menubar, tearoff=0)
        task_menu.add_command(label="Добавить задачу", command=self.open_add_task_dialog, accelerator="Ctrl+N")
        task_menu.add_command(label="Редактировать задачу", command=self.edit_selected_task, accelerator="Ctrl+E")
        task_menu.add_command(label="Удалить задачу", command=self.delete_selected_task, accelerator="Delete")
        menubar.add_cascade(label="Задача", menu=task_menu)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Сегодня", command=self.open_today_view)
        view_menu.add_command(label="В ближайшее время", command=self.open_soon_view)
        view_menu.add_command(label="Срочные", command=self.open_urgent_view)
        view_menu.add_command(label="Несрочные", command=self.open_non_urgent_view)
        view_menu.add_command(label="Матрица Эйзенхауэра", command=self.open_eisenhower_matrix)
        menubar.add_cascade(label="Вид", menu=view_menu)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Шаблоны", command=self.open_templates_window)
        menubar.add_cascade(label="Инструменты", menu=tools_menu)
        
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Настройки", command=self.open_settings_window)
        menubar.add_cascade(label="Настройки", menu=settings_menu)
        
        # Панель инструментов
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="+ Добавить", command=self.open_add_task_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏ Редакт.", command=self.edit_selected_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑 Удалить", command=self.delete_selected_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📋 Шаблоны", command=self.open_templates_window).pack(side=tk.LEFT, padx=2)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_tasks)
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.RIGHT, padx=5)
        ttk.Label(toolbar, text="🔍 Поиск:").pack(side=tk.RIGHT)
        
        # Основная панель
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Левая панель - Навигация и дерево задач
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Навигация
        nav_frame = ttk.LabelFrame(left_frame, text="НАВИГАЦИЯ")
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        nav_buttons = [
            ("📅 Сегодня", self.open_today_view),
            ("⏰ В ближайшее время", self.open_soon_view),
            ("🔴 Срочные", self.open_urgent_view),
            ("🟢 Несрочные", self.open_non_urgent_view),
            ("📊 По приоритету", self.open_priority_view),
        ]
        for text, cmd in nav_buttons:
            ttk.Button(nav_frame, text=text, command=cmd).pack(fill=tk.X, padx=2, pady=1)
        
        # Дерево задач
        tree_frame = ttk.LabelFrame(left_frame, text="ДЕРЕВО ЗАДАЧ")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ('status', 'priority')
        self.task_tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings')
        self.task_tree.heading('#0', text='Задача')
        self.task_tree.heading('status', text='Статус')
        self.task_tree.heading('priority', text='Приоритет')
        self.task_tree.column('#0', width=300)
        self.task_tree.column('status', width=80)
        self.task_tree.column('priority', width=80)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.task_tree.bind('<Double-1>', lambda e: self.edit_selected_task())
        self.task_tree.bind('<Delete>', lambda e: self.delete_selected_task())
        
        # Правая панель - Детали задачи
        details_frame = ttk.LabelFrame(main_paned, text="ДЕТАЛИ ЗАДАЧИ")
        main_paned.add(details_frame, weight=1)
        
        ttk.Label(details_frame, text="Название:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.detail_name = ttk.Entry(details_frame, state='readonly')
        self.detail_name.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(details_frame, text="Статус:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.detail_status = ttk.Combobox(details_frame, values=["Не начата", "В процессе", "Завершена", "Отложена"], state='readonly')
        self.detail_status.pack(fill=tk.X, padx=5, pady=2)
        self.detail_status.bind('<<ComboboxSelected>>', self.update_task_from_details)
        
        ttk.Label(details_frame, text="Приоритет (Важность/Срочность):").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.detail_priority = ttk.Label(details_frame, text="-/-")
        self.detail_priority.pack(anchor=tk.W, padx=5, pady=2)
        
        ttk.Label(details_frame, text="Дедлайн:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.detail_deadline = ttk.Label(details_frame, text="-")
        self.detail_deadline.pack(anchor=tk.W, padx=5, pady=2)
        
        ttk.Label(details_frame, text="Периодичность:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.detail_recurrence = ttk.Label(details_frame, text="Нет")
        self.detail_recurrence.pack(anchor=tk.W, padx=5, pady=2)
        
        ttk.Label(details_frame, text="Описание:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.detail_description = tk.Text(details_frame, height=6, state='disabled')
        self.detail_description.pack(fill=tk.X, padx=5, pady=2)
        
        files_frame = ttk.Frame(details_frame)
        files_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(files_frame, text="📎 Файлы:").pack(anchor=tk.W)
        self.detail_files = ttk.Treeview(files_frame, height=4)
        self.detail_files.pack(fill=tk.X, pady=2)
        ttk.Button(files_frame, text="Открыть файл", command=self.open_selected_file).pack(anchor=tk.W, pady=2)
        
        self.task_tree.bind('<<TreeviewSelect>>', self.on_task_select)
        
        # Статусная строка
        self.status_bar = ttk.Label(self.root, text="Готово", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Горячие клавиши
        self.root.bind('<Control-n>', lambda e: self.open_add_task_dialog())
        self.root.bind('<Control-e>', lambda e: self.edit_selected_task())
        self.root.bind('<Control-s>', lambda e: self.save_data())
        
    def refresh_task_tree(self, tasks=None):
        """Обновление дерева задач"""
        if tasks is None:
            tasks = self.tasks
        
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        status_map = {"Не начата": "○", "В процессе": "◐", "Завершена": "●", "Отложена": "⏸"}
        
        def add_tasks_to_tree(parent_tasks, parent_id=''):
            for task in parent_tasks:
                status_icon = status_map.get(task.get('status', 'Не начата'), '○')
                priority_text = f"{task.get('importance', 0)}/{task.get('urgency', 0)}"
                
                tree_id = self.task_tree.insert(parent_id, 'end', text=f"{status_icon} {task['title']}",
                                                values=(task.get('status', ''), priority_text),
                                                tags=(str(task.get('id', '')),))
                
                if 'subtasks' in task and task['subtasks']:
                    add_tasks_to_tree(task['subtasks'], tree_id)
        
        add_tasks_to_tree(tasks)
    
    def filter_tasks(self, *args):
        """Фильтрация задач по поиску"""
        search_term = self.search_var.get().lower()
        if not search_term:
            self.refresh_task_tree()
            return
        
        def filter_recursive(tasks):
            result = []
            for task in tasks:
                if search_term in task.get('title', '').lower() or search_term in task.get('description', '').lower():
                    result.append(task)
                elif 'subtasks' in task:
                    filtered_sub = filter_recursive(task['subtasks'])
                    if filtered_sub:
                        task_copy = task.copy()
                        task_copy['subtasks'] = filtered_sub
                        result.append(task_copy)
            return result
        
        filtered = filter_recursive(self.tasks)
        self.refresh_task_tree(filtered)
    
    def on_task_select(self, event=None):
        """Обработка выбора задачи"""
        selection = self.task_tree.selection()
        if not selection:
            self.clear_details()
            return
        
        item_id = selection[0]
        task = self.find_task_by_tree_id(item_id)
        
        if task:
            self.detail_name.config(state='normal')
            self.detail_name.delete(0, tk.END)
            self.detail_name.insert(0, task.get('title', ''))
            self.detail_name.config(state='readonly')
            
            self.detail_status.set(task.get('status', 'Не начата'))
            
            importance = task.get('importance', 0)
            urgency = task.get('urgency', 0)
            imp_str = "●" * importance + "○" * (5 - importance)
            urg_str = "●" * urgency + "○" * (5 - urgency)
            self.detail_priority.config(text=f"Важность: {imp_str}  Срочность: {urg_str}")
            
            deadline = task.get('deadline', '')
            self.detail_deadline.config(text=deadline if deadline else "Не установлен")
            
            recurrence = task.get('recurrence', 'Нет')
            self.detail_recurrence.config(text=recurrence)
            
            self.detail_description.config(state='normal')
            self.detail_description.delete('1.0', tk.END)
            self.detail_description.insert('1.0', task.get('description', ''))
            self.detail_description.config(state='disabled')
            
            # Файлы
            for item in self.detail_files.get_children():
                self.detail_files.delete(item)
            for f in task.get('files', []):
                self.detail_files.insert('', 'end', text=os.path.basename(f), values=(f,))
    
    def find_task_by_tree_id(self, tree_id, tasks=None):
        """Поиск задачи по ID в дереве"""
        if tasks is None:
            tasks = self.tasks
        
        for task in tasks:
            if str(task.get('id', '')) in self.task_tree.item(tree_id, 'tags'):
                return task
            if 'subtasks' in task:
                found = self.find_task_by_tree_id(tree_id, task['subtasks'])
                if found:
                    return found
        return None
    
    def find_task_by_id(self, task_id, tasks=None):
        """Поиск задачи по ID"""
        if tasks is None:
            tasks = self.tasks
        
        for task in tasks:
            if task.get('id') == task_id:
                return task, tasks
            if 'subtasks' in task:
                found, parent_list = self.find_task_by_id(task_id, task['subtasks'])
                if found:
                    return found, parent_list
        return None, None
    
    def clear_details(self):
        """Очистка панели деталей"""
        self.detail_name.config(state='normal')
        self.detail_name.delete(0, tk.END)
        self.detail_name.config(state='readonly')
        self.detail_status.set('')
        self.detail_priority.config(text='-/-')
        self.detail_deadline.config(text='-')
        self.detail_recurrence.config(text='Нет')
        self.detail_description.config(state='normal')
        self.detail_description.delete('1.0', tk.END)
        self.detail_description.config(state='disabled')
        for item in self.detail_files.get_children():
            self.detail_files.delete(item)
    
    def update_task_from_details(self, event=None):
        """Обновление задачи из панели деталей"""
        selection = self.task_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        task = self.find_task_by_tree_id(item_id)
        
        if task:
            task['status'] = self.detail_status.get()
            self.save_data()
            self.refresh_task_tree()
            self.update_status_bar()
    
    def update_status_bar(self):
        """Обновление статусной строки"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.get('status') == 'Завершена')
        in_progress = sum(1 for t in self.tasks if t.get('status') == 'В процессе')
        pending = sum(1 for t in self.tasks if t.get('status') in ['Не начата', 'Отложена'])
        
        self.status_bar.config(text=f"Всего задач: {total} | Выполнено: {completed} | В работе: {in_progress} | Ожидание: {pending}")
    
    def get_next_id(self, tasks=None):
        """Получение следующего ID"""
        if tasks is None:
            tasks = self.tasks
        
        max_id = 0
        for task in tasks:
            max_id = max(max_id, task.get('id', 0))
            if 'subtasks' in task:
                max_id = max(max_id, self.get_next_id(task['subtasks']) - 1)
        return max_id + 1
    
    def open_add_task_dialog(self, parent_id=None, template=None):
        """Открытие диалога добавления/редактирования задачи"""
        dialog = tk.Toplevel(self.root)
        dialog.title("ДОБАВЛЕНИЕ ЗАДАЧИ" if not template else "ИЗ ШАБЛОНА")
        dialog.geometry("600x700")
        dialog.transient(self.root)
        dialog.grab_set()
        
        task_data = {}
        if template:
            task_data = template.copy()
        
        # Название
        ttk.Label(dialog, text="Название задачи:").pack(anchor=tk.W, padx=20, pady=(20,5))
        name_entry = ttk.Entry(dialog, width=50)
        name_entry.pack(padx=20, fill=tk.X)
        if task_data.get('title'):
            name_entry.insert(0, task_data['title'])
        name_entry.focus()
        
        # Родительская задача
        ttk.Label(dialog, text="Родительская задача:").pack(anchor=tk.W, padx=20, pady=(15,5))
        parent_var = tk.StringVar()
        parent_combo = ttk.Combobox(dialog, textvariable=parent_var, state='readonly')
        parent_combo.pack(padx=20, fill=tk.X)
        
        parent_options = ["(Корень)"]
        def collect_titles(tasks, level=0):
            for task in tasks:
                prefix = "  " * level
                parent_options.append(f"{prefix}{task['title']} (ID:{task['id']})")
                if 'subtasks' in task:
                    collect_titles(task['subtasks'], level+1)
        collect_titles(self.tasks)
        parent_combo['values'] = parent_options
        
        if parent_id:
            parent_task, _ = self.find_task_by_id(parent_id)
            if parent_task:
                parent_var.set(f"{parent_task['title']} (ID:{parent_task['id']})")
        
        # Статус
        ttk.Label(dialog, text="Статус:").pack(anchor=tk.W, padx=20, pady=(15,5))
        status_var = tk.StringVar(value=task_data.get('status', 'Не начата'))
        status_frame = ttk.Frame(dialog)
        status_frame.pack(padx=20, fill=tk.X)
        for status in ["Не начата", "В процессе", "Завершена", "Отложена"]:
            ttk.Radiobutton(status_frame, text=status, variable=status_var, value=status).pack(side=tk.LEFT, padx=10)
        
        # Приоритет
        prio_frame = ttk.LabelFrame(dialog, text="Приоритет")
        prio_frame.pack(fill=tk.X, padx=20, pady=15)
        
        ttk.Label(prio_frame, text="Важность:").pack(anchor=tk.W, padx=5, pady=5)
        importance_scale = ttk.Scale(prio_frame, from_=1, to=5, orient=tk.HORIZONTAL, length=300)
        importance_scale.set(task_data.get('importance', 3))
        importance_scale.pack(padx=5)
        imp_label = ttk.Label(prio_frame, text="3")
        imp_label.pack()
        importance_scale.bind('<Motion>', lambda e: imp_label.config(text=str(int(importance_scale.get()))))
        
        ttk.Label(prio_frame, text="Срочность:").pack(anchor=tk.W, padx=5, pady=5)
        urgency_scale = ttk.Scale(prio_frame, from_=1, to=5, orient=tk.HORIZONTAL, length=300)
        urgency_scale.set(task_data.get('urgency', 3))
        urgency_scale.pack(padx=5)
        urg_label = ttk.Label(prio_frame, text="3")
        urg_label.pack()
        urgency_scale.bind('<Motion>', lambda e: urg_label.config(text=str(int(urgency_scale.get()))))
        
        # Сроки
        date_frame = ttk.LabelFrame(dialog, text="Сроки")
        date_frame.pack(fill=tk.X, padx=20, pady=15)
        
        ttk.Label(date_frame, text="Дедлайн:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        deadline_entry = ttk.Entry(date_frame, width=30)
        deadline_entry.grid(row=0, column=1, padx=5, pady=5)
        if task_data.get('deadline'):
            deadline_entry.insert(0, task_data['deadline'])
        
        ttk.Label(date_frame, text="Периодичность:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        recurrence_var = tk.StringVar(value=task_data.get('recurrence', 'Нет'))
        recurrence_combo = ttk.Combobox(date_frame, textvariable=recurrence_var, 
                                        values=["Нет", "Ежедневно", "Еженедельно", "Ежемесячно", "Ежегодно"])
        recurrence_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Описание
        ttk.Label(dialog, text="Описание:").pack(anchor=tk.W, padx=20, pady=(15,5))
        desc_text = tk.Text(dialog, height=8, width=60)
        desc_text.pack(padx=20, fill=tk.X)
        if task_data.get('description'):
            desc_text.insert('1.0', task_data['description'])
        
        # Вложения
        files_frame = ttk.LabelFrame(dialog, text="Вложения")
        files_frame.pack(fill=tk.X, padx=20, pady=15)
        
        files_list = task_data.get('files', [])
        
        def add_file():
            filename = filedialog.askopenfilename()
            if filename:
                files_list.append(filename)
                update_files_list()
        
        def remove_file():
            sel = files_listbox.curselection()
            if sel:
                del files_list[sel[0]]
                update_files_list()
        
        def update_files_list():
            files_listbox.delete(0, tk.END)
            for f in files_list:
                files_listbox.insert(tk.END, os.path.basename(f))
        
        ttk.Button(files_frame, text="📎 Добавить файл", command=add_file).pack(pady=5)
        files_listbox = tk.Listbox(files_frame, height=4, width=50)
        files_listbox.pack(pady=5)
        ttk.Button(files_frame, text="Удалить файл", command=remove_file).pack(pady=5)
        update_files_list()
        
        # Подзадачи из шаблона
        if task_data.get('subtasks'):
            sub_frame = ttk.LabelFrame(dialog, text="Подзадачи из шаблона")
            sub_frame.pack(fill=tk.X, padx=20, pady=15)
            
            for i, sub in enumerate(task_data['subtasks']):
                ttk.Label(sub_frame, text=f"{i+1}. {sub.get('title', 'Подзадача')} (Важн: {sub.get('importance', 3)}, Сроч: {sub.get('urgency', 3)})").pack(anchor=tk.W, padx=5)
        
        # Кнопки
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def save_task():
            title = name_entry.get().strip()
            if not title:
                messagebox.showwarning("Предупреждение", "Введите название задачи!")
                return
            
            parent_text = parent_var.get()
            target_list = self.tasks
            
            if parent_text and parent_text != "(Корень)":
                import re
                match = re.search(r'\(ID:(\d+)\)', parent_text)
                if match:
                    parent_id_val = int(match.group(1))
                    parent_task, parent_list = self.find_task_by_id(parent_id_val)
                    if parent_task:
                        if 'subtasks' not in parent_task:
                            parent_task['subtasks'] = []
                        target_list = parent_task['subtasks']
            
            new_task = {
                'id': self.get_next_id(),
                'title': title,
                'status': status_var.get(),
                'importance': int(importance_scale.get()),
                'urgency': int(urgency_scale.get()),
                'deadline': deadline_entry.get().strip(),
                'recurrence': recurrence_var.get(),
                'description': desc_text.get('1.0', tk.END).strip(),
                'files': files_list,
                'subtasks': task_data.get('subtasks', [])
            }
            
            target_list.append(new_task)
            self.save_data()
            self.refresh_task_tree()
            self.update_status_bar()
            dialog.destroy()
        
        ttk.Button(btn_frame, text="Сохранить", command=save_task).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
    
    def edit_selected_task(self):
        """Редактирование выбранной задачи"""
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showinfo("Информация", "Выберите задачу для редактирования")
            return
        
        item_id = selection[0]
        task = self.find_task_by_tree_id(item_id)
        
        if not task:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("РЕДАКТИРОВАНИЕ ЗАДАЧИ")
        dialog.geometry("600x700")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Название
        ttk.Label(dialog, text="Название задачи:").pack(anchor=tk.W, padx=20, pady=(20,5))
        name_entry = ttk.Entry(dialog, width=50)
        name_entry.pack(padx=20, fill=tk.X)
        name_entry.insert(0, task.get('title', ''))
        name_entry.focus()
        
        # Статус
        ttk.Label(dialog, text="Статус:").pack(anchor=tk.W, padx=20, pady=(15,5))
        status_var = tk.StringVar(value=task.get('status', 'Не начата'))
        status_frame = ttk.Frame(dialog)
        status_frame.pack(padx=20, fill=tk.X)
        for status in ["Не начата", "В процессе", "Завершена", "Отложена"]:
            ttk.Radiobutton(status_frame, text=status, variable=status_var, value=status).pack(side=tk.LEFT, padx=10)
        
        # Приоритет
        prio_frame = ttk.LabelFrame(dialog, text="Приоритет")
        prio_frame.pack(fill=tk.X, padx=20, pady=15)
        
        ttk.Label(prio_frame, text="Важность:").pack(anchor=tk.W, padx=5, pady=5)
        importance_scale = ttk.Scale(prio_frame, from_=1, to=5, orient=tk.HORIZONTAL, length=300)
        importance_scale.set(task.get('importance', 3))
        importance_scale.pack(padx=5)
        imp_label = ttk.Label(prio_frame, text=str(task.get('importance', 3)))
        imp_label.pack()
        importance_scale.bind('<Motion>', lambda e: imp_label.config(text=str(int(importance_scale.get()))))
        
        ttk.Label(prio_frame, text="Срочность:").pack(anchor=tk.W, padx=5, pady=5)
        urgency_scale = ttk.Scale(prio_frame, from_=1, to=5, orient=tk.HORIZONTAL, length=300)
        urgency_scale.set(task.get('urgency', 3))
        urgency_scale.pack(padx=5)
        urg_label = ttk.Label(prio_frame, text=str(task.get('urgency', 3)))
        urg_label.pack()
        urgency_scale.bind('<Motion>', lambda e: urg_label.config(text=str(int(urgency_scale.get()))))
        
        # Сроки
        date_frame = ttk.LabelFrame(dialog, text="Сроки")
        date_frame.pack(fill=tk.X, padx=20, pady=15)
        
        ttk.Label(date_frame, text="Дедлайн:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        deadline_entry = ttk.Entry(date_frame, width=30)
        deadline_entry.grid(row=0, column=1, padx=5, pady=5)
        deadline_entry.insert(0, task.get('deadline', ''))
        
        ttk.Label(date_frame, text="Периодичность:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        recurrence_var = tk.StringVar(value=task.get('recurrence', 'Нет'))
        recurrence_combo = ttk.Combobox(date_frame, textvariable=recurrence_var, 
                                        values=["Нет", "Ежедневно", "Еженедельно", "Ежемесячно", "Ежегодно"])
        recurrence_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Описание
        ttk.Label(dialog, text="Описание:").pack(anchor=tk.W, padx=20, pady=(15,5))
        desc_text = tk.Text(dialog, height=8, width=60)
        desc_text.pack(padx=20, fill=tk.X)
        desc_text.insert('1.0', task.get('description', ''))
        
        # Вложения
        files_frame = ttk.LabelFrame(dialog, text="Вложения")
        files_frame.pack(fill=tk.X, padx=20, pady=15)
        
        files_list = list(task.get('files', []))
        
        def add_file():
            filename = filedialog.askopenfilename()
            if filename:
                files_list.append(filename)
                update_files_list()
        
        def remove_file():
            sel = files_listbox.curselection()
            if sel:
                del files_list[sel[0]]
                update_files_list()
        
        def update_files_list():
            files_listbox.delete(0, tk.END)
            for f in files_list:
                files_listbox.insert(tk.END, os.path.basename(f))
        
        ttk.Button(files_frame, text="📎 Добавить файл", command=add_file).pack(pady=5)
        files_listbox = tk.Listbox(files_frame, height=4, width=50)
        files_listbox.pack(pady=5)
        ttk.Button(files_frame, text="Удалить файл", command=remove_file).pack(pady=5)
        update_files_list()
        
        # Подзадачи
        sub_frame = ttk.LabelFrame(dialog, text="Подзадачи")
        sub_frame.pack(fill=tk.X, padx=20, pady=15)
        
        def add_subtask():
            sub_dialog = tk.Toplevel(dialog)
            sub_dialog.title("Добавить подзадачу")
            sub_dialog.geometry("400x300")
            sub_dialog.transient(dialog)
            
            ttk.Label(sub_dialog, text="Название подзадачи:").pack(padx=20, pady=10)
            sub_name = ttk.Entry(sub_dialog, width=40)
            sub_name.pack(padx=20)
            
            ttk.Label(sub_dialog, text="Важность (1-5):").pack(padx=20, pady=5)
            sub_imp = ttk.Spinbox(sub_dialog, from_=1, to=5, width=10)
            sub_imp.set(3)
            sub_imp.pack(padx=20)
            
            ttk.Label(sub_dialog, text="Срочность (1-5):").pack(padx=20, pady=5)
            sub_urg = ttk.Spinbox(sub_dialog, from_=1, to=5, width=10)
            sub_urg.set(3)
            sub_urg.pack(padx=20)
            
            def save_sub():
                name = sub_name.get().strip()
                if name:
                    if 'subtasks' not in task:
                        task['subtasks'] = []
                    task['subtasks'].append({
                        'id': self.get_next_id(),
                        'title': name,
                        'importance': int(sub_imp.get()),
                        'urgency': int(sub_urg.get()),
                        'status': 'Не начата'
                    })
                    self.save_data()
                    self.refresh_task_tree()
                    sub_dialog.destroy()
                    update_subtasks_list()
            
            ttk.Button(sub_dialog, text="Добавить", command=save_sub).pack(pady=20)
            ttk.Button(sub_dialog, text="Отмена", command=sub_dialog.destroy).pack()
        
        def update_subtasks_list():
            for w in sub_frame.winfo_children()[1:]:
                w.destroy()
            
            subtasks = task.get('subtasks', [])
            for i, sub in enumerate(subtasks):
                frame = ttk.Frame(sub_frame)
                frame.pack(fill=tk.X, padx=5, pady=2)
                ttk.Label(frame, text=f"{i+1}. {sub.get('title', 'Подзадача')}").pack(side=tk.LEFT)
                
                def make_delete(idx):
                    def delete_sub():
                        if 'subtasks' in task and idx < len(task['subtasks']):
                            del task['subtasks'][idx]
                            self.save_data()
                            self.refresh_task_tree()
                            update_subtasks_list()
                    return delete_sub
                
                ttk.Button(frame, text="🗑", command=make_delete(i)).pack(side=tk.RIGHT)
        
        update_subtasks_list()
        
        ttk.Button(sub_frame, text="+ Добавить подзадачу", command=add_subtask).pack(pady=5)
        
        # Кнопки
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def save_changes():
            title = name_entry.get().strip()
            if not title:
                messagebox.showwarning("Предупреждение", "Введите название задачи!")
                return
            
            task['title'] = title
            task['status'] = status_var.get()
            task['importance'] = int(importance_scale.get())
            task['urgency'] = int(urgency_scale.get())
            task['deadline'] = deadline_entry.get().strip()
            task['recurrence'] = recurrence_var.get()
            task['description'] = desc_text.get('1.0', tk.END).strip()
            task['files'] = files_list
            
            self.save_data()
            self.refresh_task_tree()
            self.on_task_select()
            self.update_status_bar()
            dialog.destroy()
        
        ttk.Button(btn_frame, text="Сохранить", command=save_changes).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
    
    def delete_selected_task(self):
        """Удаление выбранной задачи"""
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showinfo("Информация", "Выберите задачу для удаления")
            return
        
        if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту задачу?"):
            return
        
        item_id = selection[0]
        task = self.find_task_by_tree_id(item_id)
        
        if task:
            task_id = task['id']
            found_task, parent_list = self.find_task_by_id(task_id)
            if found_task and parent_list:
                parent_list.remove(found_task)
                self.save_data()
                self.refresh_task_tree()
                self.clear_details()
                self.update_status_bar()
    
    def open_selected_file(self):
        """Открытие выбранного файла"""
        selection = self.detail_files.selection()
        if not selection:
            return
        
        item = self.detail_files.item(selection[0])
        filepath = item['values'][0] if item['values'] else None
        
        if filepath and os.path.exists(filepath):
            if os.name == 'nt':
                os.startfile(filepath)
            else:
                subprocess.call(['xdg-open', filepath])
        else:
            messagebox.showwarning("Предупреждение", "Файл не найден")
    
    def open_templates_window(self):
        """Открытие окна шаблонов"""
        window = tk.Toplevel(self.root)
        window.title("ШАБЛОНЫ ЗАДАЧ")
        window.geometry("800x600")
        window.transient(self.root)
        
        # Список шаблонов
        list_frame = ttk.LabelFrame(window, text="СПИСОК ШАБЛОНОВ")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        templates_listbox = tk.Listbox(list_frame, width=40, height=20)
        templates_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        for t in self.templates:
            templates_listbox.insert(tk.END, f"📋 {t['name']} ({t.get('category', '')})")
        
        def select_template(event):
            sel = templates_listbox.curselection()
            if sel:
                idx = sel[0]
                template = self.templates[idx]
                
                for w in details_frame.winfo_children():
                    w.destroy()
                
                ttk.Label(details_frame, text=f"Название: {template['name']}").pack(anchor=tk.W, padx=5)
                ttk.Label(details_frame, text=f"Категория: {template.get('category', '')}").pack(anchor=tk.W, padx=5)
                ttk.Label(details_frame, text=f"Описание: {template.get('description', '')}").pack(anchor=tk.W, padx=5)
                
                ttk.Label(details_frame, text="Структура подзадач:").pack(anchor=tk.W, padx=5, pady=(10,0))
                for i, sub in enumerate(template.get('subtasks', [])):
                    ttk.Label(details_frame, text=f"  {i+1}. {sub.get('title', '')} (В: {sub.get('importance', 3)}, С: {sub.get('urgency', 3)})").pack(anchor=tk.W, padx=15)
        
        templates_listbox.bind('<<ListboxSelect>>', select_template)
        
        # Детали
        details_frame = ttk.LabelFrame(window, text="ДЕТАЛИ ШАБЛОНА")
        details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Кнопки управления
        btn_frame = ttk.Frame(window)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        def apply_template():
            sel = templates_listbox.curselection()
            if not sel:
                messagebox.showinfo("Информация", "Выберите шаблон")
                return
            
            template = self.templates[sel[0]]
            self.open_add_task_dialog(template=template)
        
        def new_template():
            t_dialog = tk.Toplevel(window)
            t_dialog.title("Новый шаблон")
            t_dialog.geometry("500x500")
            t_dialog.transient(window)
            
            ttk.Label(t_dialog, text="Название:").pack(padx=20, pady=5)
            name_entry = ttk.Entry(t_dialog, width=40)
            name_entry.pack(padx=20)
            
            ttk.Label(t_dialog, text="Категория:").pack(padx=20, pady=5)
            cat_entry = ttk.Entry(t_dialog, width=40)
            cat_entry.pack(padx=20)
            
            ttk.Label(t_dialog, text="Описание:").pack(padx=20, pady=5)
            desc_text = tk.Text(t_dialog, height=5, width=40)
            desc_text.pack(padx=20)
            
            subtasks = []
            
            def add_subtask():
                s_dialog = tk.Toplevel(t_dialog)
                s_dialog.title("Подзадача шаблона")
                s_dialog.geometry("300x200")
                
                ttk.Label(s_dialog, text="Название:").pack(padx=10, pady=5)
                s_name = ttk.Entry(s_dialog, width=30)
                s_name.pack(padx=10)
                
                ttk.Label(s_dialog, text="Важность:").pack(padx=10, pady=5)
                s_imp = ttk.Spinbox(s_dialog, from_=1, to=5, width=10)
                s_imp.set(3)
                s_imp.pack(padx=10)
                
                ttk.Label(s_dialog, text="Срочность:").pack(padx=10, pady=5)
                s_urg = ttk.Spinbox(s_dialog, from_=1, to=5, width=10)
                s_urg.set(3)
                s_urg.pack(padx=10)
                
                def save():
                    name = s_name.get().strip()
                    if name:
                        subtasks.append({
                            'title': name,
                            'importance': int(s_imp.get()),
                            'urgency': int(s_urg.get())
                        })
                        s_dialog.destroy()
                
                ttk.Button(s_dialog, text="Добавить", command=save).pack(pady=10)
                ttk.Button(s_dialog, text="Отмена", command=s_dialog.destroy).pack()
            
            ttk.Button(t_dialog, text="+ Добавить подзадачу", command=add_subtask).pack(pady=5)
            
            def save_template():
                name = name_entry.get().strip()
                if not name:
                    messagebox.showwarning("Предупреждение", "Введите название шаблона")
                    return
                
                new_t = {
                    'id': len(self.templates) + 1,
                    'name': name,
                    'category': cat_entry.get().strip(),
                    'description': desc_text.get('1.0', tk.END).strip(),
                    'subtasks': subtasks
                }
                self.templates.append(new_t)
                self.save_data()
                templates_listbox.insert(tk.END, f"📋 {name}")
                t_dialog.destroy()
            
            ttk.Button(t_dialog, text="Сохранить", command=save_template).pack(pady=10)
            ttk.Button(t_dialog, text="Отмена", command=t_dialog.destroy).pack()
        
        def delete_template():
            sel = templates_listbox.curselection()
            if not sel:
                messagebox.showinfo("Информация", "Выберите шаблон")
                return
            
            if messagebox.askyesno("Подтверждение", "Удалить шаблон?"):
                del self.templates[sel[0]]
                self.save_data()
                templates_listbox.delete(sel[0])
                for w in details_frame.winfo_children():
                    w.destroy()
        
        ttk.Button(btn_frame, text="Применить", command=apply_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="+ Новый шаблон", command=new_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑 Удалить", command=delete_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Закрыть", command=window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def open_today_view(self):
        """Открытие представления 'Сегодня'"""
        window = tk.Toplevel(self.root)
        window.title("ЗАДАЧИ НА СЕГОДНЯ")
        window.geometry("900x600")
        
        today = datetime.now().strftime("%d.%m.%Y")
        weekday = datetime.now().strftime("%A")
        weekdays_ru = {"Monday": "Понедельник", "Tuesday": "Вторник", "Wednesday": "Среда", 
                       "Thursday": "Четверг", "Friday": "Пятница", "Saturday": "Суббота", "Sunday": "Воскресенье"}
        weekday_ru = weekdays_ru.get(weekday, weekday)
        
        ttk.Label(window, text=f"{weekday_ru}, {today}", font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Фильтрация задач
        urgent_tasks = []
        important_tasks = []
        planned_tasks = []
        
        def collect_tasks(tasks):
            for task in tasks:
                deadline = task.get('deadline', '')
                importance = task.get('importance', 0)
                urgency = task.get('urgency', 0)
                
                is_today = today in deadline if deadline else False
                
                if is_today or urgency >= 4:
                    urgent_tasks.append(f"□ {task['title']} (Срочность: {'●'*urgency}{'○'*(5-urgency)})")
                elif importance >= 4:
                    important_tasks.append(f"□ {task['title']} (Важность: {'●'*importance}{'○'*(5-importance)})")
                else:
                    planned_tasks.append(f"□ {task['title']} (Важность: {'●'*importance}{'○'*(5-importance)})")
                
                if 'subtasks' in task:
                    collect_tasks(task['subtasks'])
        
        collect_tasks(self.tasks)
        
        # Срочные
        urgent_frame = ttk.LabelFrame(window, text="🔴 СРОЧНЫЕ ЗАДАЧИ")
        urgent_frame.pack(fill=tk.X, padx=10, pady=5)
        for t in urgent_tasks[:10]:
            ttk.Label(urgent_frame, text=t).pack(anchor=tk.W, padx=5)
        
        # Важные
        imp_frame = ttk.LabelFrame(window, text="🟡 ВАЖНЫЕ ЗАДАЧИ")
        imp_frame.pack(fill=tk.X, padx=10, pady=5)
        for t in important_tasks[:10]:
            ttk.Label(imp_frame, text=t).pack(anchor=tk.W, padx=5)
        
        # Плановые
        plan_frame = ttk.LabelFrame(window, text="🟢 ПЛАНОВЫЕ ЗАДАЧИ")
        plan_frame.pack(fill=tk.X, padx=10, pady=5)
        for t in planned_tasks[:10]:
            ttk.Label(plan_frame, text=t).pack(anchor=tk.W, padx=5)
        
        ttk.Button(window, text="Закрыть", command=window.destroy).pack(pady=10)
    
    def open_soon_view(self):
        """Открытие представления 'В ближайшее время'"""
        window = tk.Toplevel(self.root)
        window.title("В БЛИЖАЙШЕЕ ВРЕМЯ")
        window.geometry("700x500")
        
        ttk.Label(window, text="Задачи на ближайшие 7 дней", font=('Arial', 14, 'bold')).pack(pady=10)
        
        soon_frame = ttk.Frame(window)
        soon_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tree = ttk.Treeview(soon_frame, columns=('deadline', 'priority'), show='headings')
        tree.heading('#0', text='Задача')
        tree.heading('deadline', text='Дедлайн')
        tree.heading('priority', text='Приоритет')
        tree.column('#0', width=300)
        tree.column('deadline', width=150)
        tree.column('priority', width=100)
        tree.pack(fill=tk.BOTH, expand=True)
        
        today = datetime.now()
        week_later = today + timedelta(days=7)
        
        def add_tasks(tasks):
            for task in tasks:
                deadline = task.get('deadline', '')
                if deadline:
                    try:
                        dl_date = datetime.strptime(deadline.split()[0], "%d.%m.%Y")
                        if today <= dl_date <= week_later:
                            tree.insert('', 'end', text=task['title'], 
                                       values=(deadline, f"{task.get('importance', 0)}/{task.get('urgency', 0)}"))
                    except:
                        pass
                if 'subtasks' in task:
                    add_tasks(task['subtasks'])
        
        add_tasks(self.tasks)
        ttk.Button(window, text="Закрыть", command=window.destroy).pack(pady=10)
    
    def open_urgent_view(self):
        """Открытие представления 'Срочные'"""
        window = tk.Toplevel(self.root)
        window.title("СРОЧНЫЕ ЗАДАЧИ")
        window.geometry("700x500")
        
        ttk.Label(window, text="Задачи с высокой срочностью (4-5)", font=('Arial', 14, 'bold')).pack(pady=10)
        
        tree = ttk.Treeview(window, columns=('urgency', 'status'), show='headings')
        tree.heading('#0', text='Задача')
        tree.heading('urgency', text='Срочность')
        tree.heading('status', text='Статус')
        tree.column('#0', width=350)
        tree.column('urgency', width=100)
        tree.column('status', width=100)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def add_urgent(tasks):
            for task in tasks:
                if task.get('urgency', 0) >= 4:
                    tree.insert('', 'end', text=task['title'],
                               values=(task.get('urgency', 0), task.get('status', '')))
                if 'subtasks' in task:
                    add_urgent(task['subtasks'])
        
        add_urgent(self.tasks)
        ttk.Button(window, text="Закрыть", command=window.destroy).pack(pady=10)
    
    def open_non_urgent_view(self):
        """Открытие представления 'Несрочные'"""
        window = tk.Toplevel(self.root)
        window.title("НЕСРОЧНЫЕ ЗАДАЧИ")
        window.geometry("700x500")
        
        ttk.Label(window, text="Задачи с низкой срочностью (1-2)", font=('Arial', 14, 'bold')).pack(pady=10)
        
        tree = ttk.Treeview(window, columns=('urgency', 'importance'), show='headings')
        tree.heading('#0', text='Задача')
        tree.heading('urgency', text='Срочность')
        tree.heading('importance', text='Важность')
        tree.column('#0', width=350)
        tree.column('urgency', width=100)
        tree.column('importance', width=100)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def add_non_urgent(tasks):
            for task in tasks:
                if task.get('urgency', 0) <= 2:
                    tree.insert('', 'end', text=task['title'],
                               values=(task.get('urgency', 0), task.get('importance', 0)))
                if 'subtasks' in task:
                    add_non_urgent(task['subtasks'])
        
        add_non_urgent(self.tasks)
        ttk.Button(window, text="Закрыть", command=window.destroy).pack(pady=10)
    
    def open_priority_view(self):
        """Открытие представления 'По приоритету'"""
        window = tk.Toplevel(self.root)
        window.title("ЗАДАЧИ ПО ПРИОРИТЕТУ")
        window.geometry("700x500")
        
        ttk.Label(window, text="Сортировка по приоритету (Важность × Срочность)", font=('Arial', 14, 'bold')).pack(pady=10)
        
        tree = ttk.Treeview(window, columns=('priority', 'status'), show='headings')
        tree.heading('#0', text='Задача')
        tree.heading('priority', text='Приоритет')
        tree.heading('status', text='Статус')
        tree.column('#0', width=300)
        tree.column('priority', width=100)
        tree.column('status', width=100)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        all_tasks = []
        def collect(tasks):
            for task in tasks:
                priority = task.get('importance', 0) * task.get('urgency', 0)
                all_tasks.append((task, priority))
                if 'subtasks' in task:
                    collect(task['subtasks'])
        
        collect(self.tasks)
        all_tasks.sort(key=lambda x: x[1], reverse=True)
        
        for task, priority in all_tasks:
            tree.insert('', 'end', text=task['title'],
                       values=(priority, task.get('status', '')))
        
        ttk.Button(window, text="Закрыть", command=window.destroy).pack(pady=10)
    
    def open_eisenhower_matrix(self):
        """Открытие матрицы Эйзенхауэра"""
        window = tk.Toplevel(self.root)
        window.title("МАТРИЦА ПРИОРИТЕТОВ (ЭЙЗЕНХАУЭРА)")
        window.geometry("1000x700")
        
        main_frame = ttk.Frame(window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        quadrants = {
            "urgent_important": {"title": "🔴 СРОЧНЫЕ И ВАЖНЫЕ\nСделать немедленно", "tasks": [], "color": "#ffcccc"},
            "not_urgent_important": {"title": "🟢 НЕСРОЧНЫЕ, НО ВАЖНЫЕ\nЗапланировать", "tasks": [], "color": "#ccffcc"},
            "urgent_not_important": {"title": "🟡 СРОЧНЫЕ, НО НЕ ВАЖНЫЕ\nДелегировать", "tasks": [], "color": "#ffffcc"},
            "not_urgent_not_important": {"title": "⚪ НЕСРОЧНЫЕ И НЕ ВАЖНЫЕ\nУстранить", "tasks": [], "color": "#f0f0f0"}
        }
        
        def classify_tasks(tasks):
            for task in tasks:
                imp = task.get('importance', 0)
                urg = task.get('urgency', 0)
                
                if urg >= 4 and imp >= 4:
                    quadrants["urgent_important"]["tasks"].append(task['title'])
                elif urg <= 3 and imp >= 4:
                    quadrants["not_urgent_important"]["tasks"].append(task['title'])
                elif urg >= 4 and imp <= 3:
                    quadrants["urgent_not_important"]["tasks"].append(task['title'])
                else:
                    quadrants["not_urgent_not_important"]["tasks"].append(task['title'])
                
                if 'subtasks' in task:
                    classify_tasks(task['subtasks'])
        
        classify_tasks(self.tasks)
        
        for i, (key, data) in enumerate(quadrants.items()):
            row = i // 2
            col = i % 2
            
            frame = tk.Frame(main_frame, bg=data["color"], relief=tk.RAISED, borderwidth=2)
            frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            main_frame.grid_rowconfigure(row, weight=1)
            main_frame.grid_columnconfigure(col, weight=1)
            
            ttk.Label(frame, text=data["title"], font=('Arial', 12, 'bold'), background=data["color"]).pack(pady=5)
            
            listbox = tk.Listbox(frame, height=8, bg=data["color"], relief=tk.FLAT)
            listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            for task in data["tasks"][:15]:
                listbox.insert(tk.END, f"• {task}")
        
        ttk.Button(window, text="Закрыть", command=window.destroy).pack(pady=10)
    
    def open_settings_window(self):
        """Открытие окна настроек"""
        window = tk.Toplevel(self.root)
        window.title("НАСТРОЙКИ")
        window.geometry("600x500")
        window.transient(self.root)
        
        notebook = ttk.Notebook(window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Общие настройки
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="Общие")
        
        ttk.Label(general_frame, text="Язык интерфейса:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        lang_var = tk.StringVar(value=self.settings.get('language', 'Russian'))
        lang_combo = ttk.Combobox(general_frame, textvariable=lang_var, values=["Russian", "English", "Belarusian"])
        lang_combo.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(general_frame, text="Тема оформления:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        theme_var = tk.StringVar(value=self.settings.get('theme', 'Light'))
        theme_combo = ttk.Combobox(general_frame, textvariable=theme_var, values=["Light", "Dark"])
        theme_combo.grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(general_frame, text="Начало рабочей недели:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        week_var = tk.StringVar(value=self.settings.get('week_start', 'Monday'))
        week_combo = ttk.Combobox(general_frame, textvariable=week_var, values=["Monday", "Sunday"])
        week_combo.grid(row=2, column=1, padx=10, pady=10)
        
        ttk.Label(general_frame, text="Формат даты:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        date_var = tk.StringVar(value=self.settings.get('date_format', '%d.%m.%Y'))
        date_combo = ttk.Combobox(general_frame, textvariable=date_var, values=["%d.%m.%Y", "%m/%d/%Y", "%Y-%m-%d"])
        date_combo.grid(row=3, column=1, padx=10, pady=10)
        
        ttk.Label(general_frame, text="Формат времени:").grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
        time_var = tk.StringVar(value=self.settings.get('time_format', '24h'))
        time_combo = ttk.Combobox(general_frame, textvariable=time_var, values=["24h", "12h"])
        time_combo.grid(row=4, column=1, padx=10, pady=10)
        
        # Уведомления
        notify_frame = ttk.Frame(notebook)
        notebook.add(notify_frame, text="Уведомления")
        
        notify_enabled = tk.BooleanVar(value=self.settings.get('notifications_enabled', True))
        ttk.Checkbutton(notify_frame, text="Включить уведомления", variable=notify_enabled).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        
        ttk.Label(notify_frame, text="Напоминания о дедлайнах за:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        reminder_var = tk.StringVar(value=str(self.settings.get('reminder_before', 30)))
        reminder_combo = ttk.Combobox(notify_frame, textvariable=reminder_var, values=["15 минут", "30 минут", "1 час", "2 часа"])
        reminder_combo.grid(row=1, column=1, padx=10, pady=10)
        
        sound_enabled = tk.BooleanVar(value=self.settings.get('sound_notifications', True))
        ttk.Checkbutton(notify_frame, text="Звуковые уведомления", variable=sound_enabled).grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        
        popup_enabled = tk.BooleanVar(value=self.settings.get('popup_notifications', True))
        ttk.Checkbutton(notify_frame, text="Всплывающие уведомления", variable=popup_enabled).grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        
        # Тайм-менеджмент
        tm_frame = ttk.Frame(notebook)
        notebook.add(tm_frame, text="Тайм-менеджмент")
        
        eisenhower_enabled = tk.BooleanVar(value=self.settings.get('eisenhower_matrix', True))
        ttk.Checkbutton(tm_frame, text="Использовать матрицу Эйзенхауэра", variable=eisenhower_enabled).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        
        pomodoro_enabled = tk.BooleanVar(value=self.settings.get('pomodoro_enabled', False))
        ttk.Checkbutton(tm_frame, text="Включить метод Pomodoro", variable=pomodoro_enabled).grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        
        ttk.Label(tm_frame, text="Длительность фокуса (минут):").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        focus_var = tk.StringVar(value=str(self.settings.get('pomodoro_focus', 25)))
        focus_spin = ttk.Spinbox(tm_frame, textvariable=focus_var, from_=15, to=60, width=10)
        focus_spin.grid(row=2, column=1, padx=10, pady=10)
        
        ttk.Label(tm_frame, text="Перерыв (минут):").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        break_var = tk.StringVar(value=str(self.settings.get('pomodoro_break', 5)))
        break_spin = ttk.Spinbox(tm_frame, textvariable=break_var, from_=3, to=30, width=10)
        break_spin.grid(row=3, column=1, padx=10, pady=10)
        
        # Кнопки
        btn_frame = ttk.Frame(window)
        btn_frame.pack(pady=20)
        
        def save_settings():
            self.settings['language'] = lang_var.get()
            self.settings['theme'] = theme_var.get()
            self.settings['week_start'] = week_var.get()
            self.settings['date_format'] = date_var.get()
            self.settings['time_format'] = time_var.get()
            self.settings['notifications_enabled'] = notify_enabled.get()
            self.settings['reminder_before'] = int(reminder_var.get().split()[0])
            self.settings['sound_notifications'] = sound_enabled.get()
            self.settings['popup_notifications'] = popup_enabled.get()
            self.settings['eisenhower_matrix'] = eisenhower_enabled.get()
            self.settings['pomodoro_enabled'] = pomodoro_enabled.get()
            self.settings['pomodoro_focus'] = int(focus_var.get())
            self.settings['pomodoro_break'] = int(break_var.get())
            
            self.save_data()
            messagebox.showinfo("Сохранено", "Настройки сохранены")
            window.destroy()
        
        ttk.Button(btn_frame, text="Сохранить", command=save_settings).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=window.destroy).pack(side=tk.LEFT, padx=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = TaskOrganizer(root)
    root.mainloop()
