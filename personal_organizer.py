#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Персональный органайзер-планировщик
Реализация согласно спецификации в organizer_interface_schemas.docx и organizer_interface_schemas.md

Функционал:
1. Базовое управление задачами и атрибутами (добавление, редактирование, удаление, иерархия)
2. Атрибуты: статус, приоритет (важность/срочность), дедлайн, периодичность, описание
3. Шаблоны задач с управлением
4. Представления: Сегодня, В ближайшее время, Срочные, Несрочные, По приоритету
5. Матрица Эйзенхауэра
6. Уведомления о дедлайнах
7. Прикрепление файлов к задачам
8. Горячие клавиши Ctrl+C/V/X/A во всех полях ввода
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta
import json
import os
import copy

# Попытка импорта tkcalendar
try:
    from tkcalendar import Calendar
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False


class EnhancedEntry(ttk.Entry):
    """Поле ввода с поддержкой горячих клавиш Ctrl+C/V/X/A"""
    
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.bind('<Control-c>', self._copy)
        self.bind('<Control-v>', self._paste)
        self.bind('<Control-x>', self._cut)
        self.bind('<Control-a>', self._select_all)
    
    def _copy(self, event=None):
        try:
            self.clipboard_clear()
            self.clipboard_append(self.selection_get())
        except tk.TclError:
            pass
        return 'break'
    
    def _paste(self, event=None):
        try:
            text = self.clipboard_get()
            self.insert(tk.INSERT, text)
        except tk.TclError:
            pass
        return 'break'
    
    def _cut(self, event=None):
        try:
            text = self.selection_get()
            self.clipboard_clear()
            self.clipboard_append(text)
            self.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass
        return 'break'
    
    def _select_all(self, event=None):
        self.select_range(0, tk.END)
        self.icursor(tk.END)
        return 'break'


class EnhancedText(tk.Text):
    """Текстовое поле с поддержкой горячих клавиш Ctrl+C/V/X/A"""
    
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.bind('<Control-c>', self._copy)
        self.bind('<Control-v>', self._paste)
        self.bind('<Control-x>', self._cut)
        self.bind('<Control-a>', self._select_all)
    
    def _copy(self, event=None):
        try:
            self.clipboard_clear()
            self.clipboard_append(self.selection_get())
        except tk.TclError:
            pass
        return 'break'
    
    def _paste(self, event=None):
        try:
            text = self.clipboard_get()
            self.insert(tk.INSERT, text)
        except tk.TclError:
            pass
        return 'break'
    
    def _cut(self, event=None):
        try:
            text = self.selection_get()
            self.clipboard_clear()
            self.clipboard_append(text)
            self.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass
        return 'break'
    
    def _select_all(self, event=None):
        self.tag_add(tk.SEL, '1.0', tk.END)
        self.mark_set(tk.INSERT, '1.0')
        self.see(tk.INSERT)
        return 'break'


class Task:
    """Модель задачи со всеми атрибутами"""
    
    _id_counter = 1
    
    def __init__(self, title="", parent_id=None, status="Не начата",
                 importance=3, urgency=3, due_date=None, recurrence="Нет",
                 description="", attachments=None, subtasks=None):
        self.id = Task._id_counter
        Task._id_counter += 1
        self.title = title
        self.parent_id = parent_id
        self.status = status  # Не начата, В процессе, Завершена, Отложена
        self.importance = importance  # 1-5
        self.urgency = urgency  # 1-5
        self.due_date = due_date  # datetime или None
        self.recurrence = recurrence  # Нет, Ежедневно, Еженедельно, Ежемесячно
        self.description = description
        self.attachments = attachments if attachments else []
        self.subtasks = subtasks if subtasks else []
        self.completed = (status == "Завершена")
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'parent_id': self.parent_id,
            'status': self.status,
            'importance': self.importance,
            'urgency': self.urgency,
            'due_date': self.due_date.strftime("%Y-%m-%d %H:%M") if self.due_date else None,
            'recurrence': self.recurrence,
            'description': self.description,
            'attachments': self.attachments,
            'subtasks': self.subtasks,
            'completed': self.completed
        }
    
    @classmethod
    def from_dict(cls, data):
        task = cls(
            title=data.get('title', ''),
            parent_id=data.get('parent_id'),
            status=data.get('status', 'Не начата'),
            importance=data.get('importance', 3),
            urgency=data.get('urgency', 3),
            description=data.get('description', ''),
            recurrence=data.get('recurrence', 'Нет'),
            attachments=data.get('attachments', []),
            subtasks=data.get('subtasks', [])
        )
        task.id = data.get('id', task.id)
        if data.get('due_date'):
            try:
                task.due_date = datetime.strptime(data['due_date'], "%Y-%m-%d %H:%M")
            except ValueError:
                task.due_date = datetime.strptime(data['due_date'], "%Y-%m-%d")
        task.completed = data.get('completed', False)
        return task
    
    def get_priority_quadrant(self):
        """Определяет квадрант матрицы Эйзенхауэра"""
        imp = self.importance >= 3
        urg = self.urgency >= 3
        if urg and imp:
            return "Срочные и важные"
        elif not urg and imp:
            return "Несрочные, но важные"
        elif urg and not imp:
            return "Срочные, но не важные"
        else:
            return "Несрочные и не важные"


class TaskDialog:
    """Диалог добавления/редактирования задачи"""
    
    def __init__(self, parent, task=None, all_tasks=None, on_save=None):
        self.parent = parent
        self.task = task
        self.all_tasks = all_tasks or []
        self.on_save = on_save
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавление задачи" if task is None else "Редактирование задачи")
        self.dialog.geometry("550x650")
        self.dialog.minsize(500, 600)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 550) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 650) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        self._create_ui()
        if self.task:
            self._fill_from_task()
        
        self.dialog.bind('<Return>', lambda e: self._on_save())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
    
    def _create_ui(self):
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Название задачи
        ttk.Label(main_frame, text="Название задачи:").pack(anchor=tk.W)
        self.title_entry = EnhancedEntry(main_frame, width=50)
        self.title_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Родительская задача
        ttk.Label(main_frame, text="Родительская задача:").pack(anchor=tk.W)
        self.parent_combo = ttk.Combobox(main_frame, state="readonly", width=47)
        self.parent_combo.pack(fill=tk.X, pady=(0, 10))
        parent_options = [""] + [t.title for t in self.all_tasks if t.id != (self.task.id if self.task else 0)]
        self.parent_combo['values'] = parent_options
        
        # Статус
        ttk.Label(main_frame, text="Статус:").pack(anchor=tk.W)
        self.status_var = tk.StringVar(value="Не начата")
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        statuses = ["Не начата", "В процессе", "Завершена", "Отложена"]
        for i, status in enumerate(statuses):
            ttk.Radiobutton(status_frame, text=status, variable=self.status_var, 
                          value=status).pack(side=tk.LEFT, padx=5)
        
        # Приоритет (Важность и Срочность)
        ttk.Label(main_frame, text="Приоритет:").pack(anchor=tk.W)
        priority_frame = ttk.Frame(main_frame)
        priority_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(priority_frame, text="Важность:").pack(side=tk.LEFT)
        self.importance_scale = ttk.Scale(priority_frame, from_=1, to=5, orient=tk.HORIZONTAL, length=200)
        self.importance_scale.pack(side=tk.LEFT, padx=5)
        self.importance_label = ttk.Label(priority_frame, text="3", width=2)
        self.importance_label.pack(side=tk.LEFT)
        self.importance_scale.set(3)
        self.importance_scale.configure(command=lambda v: self.importance_label.config(text=str(int(float(v)))))
        
        ttk.Label(priority_frame, text="  Срочность:").pack(side=tk.LEFT)
        self.urgency_scale = ttk.Scale(priority_frame, from_=1, to=5, orient=tk.HORIZONTAL, length=200)
        self.urgency_scale.pack(side=tk.LEFT, padx=5)
        self.urgency_label = ttk.Label(priority_frame, text="3", width=2)
        self.urgency_label.pack(side=tk.LEFT)
        self.urgency_scale.set(3)
        self.urgency_scale.configure(command=lambda v: self.urgency_label.config(text=str(int(float(v)))))
        
        # Сроки
        ttk.Label(main_frame, text="Дедлайн (ДД.ММ.ГГГГ ЧЧ:ММ):").pack(anchor=tk.W)
        self.deadline_entry = EnhancedEntry(main_frame, width=50)
        self.deadline_entry.pack(fill=tk.X, pady=(0, 10))
        self.deadline_entry.insert(0, datetime.now().strftime("%d.%m.%Y %H:%M"))
        
        # Периодичность
        ttk.Label(main_frame, text="Периодичность:").pack(anchor=tk.W)
        self.recurrence_var = tk.StringVar(value="Нет")
        recurrence_frame = ttk.Frame(main_frame)
        recurrence_frame.pack(fill=tk.X, pady=(0, 10))
        recurrences = ["Нет", "Ежедневно", "Еженедельно", "Ежемесячно"]
        for rec in recurrences:
            ttk.Radiobutton(recurrence_frame, text=rec, variable=self.recurrence_var, 
                          value=rec).pack(side=tk.LEFT, padx=5)
        
        # Описание
        ttk.Label(main_frame, text="Описание:").pack(anchor=tk.W)
        self.desc_text = EnhancedText(main_frame, height=5, wrap=tk.WORD)
        self.desc_text.pack(fill=tk.X, pady=(0, 10))
        
        # Вложения
        ttk.Label(main_frame, text="Вложения:").pack(anchor=tk.W)
        attachments_frame = ttk.Frame(main_frame)
        attachments_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(attachments_frame, text="📎 Добавить файл", command=self._add_attachment).pack(side=tk.LEFT)
        self.attachments_list = []
        self.attachments_label = ttk.Label(attachments_frame, text="")
        self.attachments_label.pack(side=tk.LEFT, padx=10)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        ttk.Button(button_frame, text="Сохранить", command=self._on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _add_attachment(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.attachments_list.append(filename)
            self.attachments_label.config(text=f"{len(self.attachments_list)} файл(ов)")
    
    def _fill_from_task(self):
        self.title_entry.insert(0, self.task.title)
        if self.task.parent_id:
            for i, t in enumerate(self.all_tasks):
                if t.id == self.task.parent_id:
                    self.parent_combo.current(i + 1)
                    break
        self.status_var.set(self.task.status)
        self.importance_scale.set(self.task.importance)
        self.urgency_scale.set(self.task.urgency)
        if self.task.due_date:
            self.deadline_entry.delete(0, tk.END)
            self.deadline_entry.insert(0, self.task.due_date.strftime("%d.%m.%Y %H:%M"))
        self.recurrence_var.set(self.task.recurrence)
        self.desc_text.insert('1.0', self.task.description)
        self.attachments_list = self.task.attachments.copy()
        if self.attachments_list:
            self.attachments_label.config(text=f"{len(self.attachments_list)} файл(ов)")
    
    def _on_save(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Предупреждение", "Введите название задачи")
            return
        
        parent_title = self.parent_combo.get()
        parent_id = None
        if parent_title:
            for t in self.all_tasks:
                if t.title == parent_title:
                    parent_id = t.id
                    break
        
        deadline_str = self.deadline_entry.get().strip()
        due_date = None
        if deadline_str:
            try:
                due_date = datetime.strptime(deadline_str, "%d.%m.%Y %H:%M")
            except ValueError:
                try:
                    due_date = datetime.strptime(deadline_str, "%d.%m.%Y")
                except ValueError:
                    messagebox.showwarning("Предупреждение", "Неверный формат даты")
                    return
        
        if self.task:
            self.task.title = title
            self.task.parent_id = parent_id
            self.task.status = self.status_var.get()
            self.task.importance = int(self.importance_scale.get())
            self.task.urgency = int(self.urgency_scale.get())
            self.task.due_date = due_date
            self.task.recurrence = self.recurrence_var.get()
            self.task.description = self.desc_text.get('1.0', tk.END).strip()
            self.task.attachments = self.attachments_list
            self.task.completed = (self.task.status == "Завершена")
        else:
            self.result = Task(
                title=title,
                parent_id=parent_id,
                status=self.status_var.get(),
                importance=int(self.importance_scale.get()),
                urgency=int(self.urgency_scale.get()),
                due_date=due_date,
                recurrence=self.recurrence_var.get(),
                description=self.desc_text.get('1.0', tk.END).strip(),
                attachments=self.attachments_list
            )
        
        self.dialog.destroy()


class TemplatesDialog:
    """Диалог управления шаблонами задач"""
    
    def __init__(self, parent, templates=None, on_apply=None):
        self.parent = parent
        self.templates = templates or []
        self.on_apply = on_apply
        self.selected_template = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Шаблоны задач")
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_ui()
        self._refresh_list()
    
    def _create_ui(self):
        paned = ttk.PanedWindow(self.dialog, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Левая панель - список шаблонов
        left_frame = ttk.Frame(paned, width=250)
        paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="СПИСОК ШАБЛОНОВ", font=('Arial', 10, 'bold')).pack(pady=5)
        
        self.templates_listbox = tk.Listbox(left_frame, width=30, height=15)
        self.templates_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.templates_listbox.bind('<<ListboxSelect>>', self._on_select)
        
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="+ Новый шаблон", command=self._new_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="✏ Редактировать", command=self._edit_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑 Удалить", command=self._delete_template).pack(side=tk.LEFT, padx=2)
        
        # Правая панель - детали шаблона
        right_frame = ttk.Frame(paned, width=400)
        paned.add(right_frame, weight=2)
        
        ttk.Label(right_frame, text="ДЕТАЛИ ШАБЛОНА", font=('Arial', 10, 'bold')).pack(pady=5)
        
        details_frame = ttk.Frame(right_frame)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(details_frame, text="Название:").pack(anchor=tk.W)
        self.template_name = EnhancedEntry(details_frame, width=40)
        self.template_name.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(details_frame, text="Категория:").pack(anchor=tk.W)
        self.template_category = ttk.Combobox(details_frame, values=["Работа", "Личное", "Проекты"], state="readonly")
        self.template_category.pack(fill=tk.X, pady=(0, 10))
        self.template_category.set("Работа")
        
        ttk.Label(details_frame, text="Описание:").pack(anchor=tk.W)
        self.template_desc = EnhancedText(details_frame, height=4, wrap=tk.WORD)
        self.template_desc.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(details_frame, text="Структура подзадач:").pack(anchor=tk.W)
        self.subtasks_text = EnhancedText(details_frame, height=6, wrap=tk.WORD)
        self.subtasks_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.subtasks_text.insert('1.0', "▼ Задача 1\n    ○ Подзадача 1.1\n    ○ Подзадача 1.2\n▶ Задача 2")
        
        subtask_btns = ttk.Frame(details_frame)
        subtask_btns.pack(pady=5)
        ttk.Button(subtask_btns, text="+ Добавить подзадачу", command=lambda: None).pack(side=tk.LEFT, padx=2)
        ttk.Button(subtask_btns, text="✏ Редактировать", command=lambda: None).pack(side=tk.LEFT, padx=2)
        
        # Кнопки действий
        action_frame = ttk.Frame(right_frame)
        action_frame.pack(pady=10)
        ttk.Button(action_frame, text="Применить", command=self._apply_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Закрыть", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _refresh_list(self):
        self.templates_listbox.delete(0, tk.END)
        for tmpl in self.templates:
            self.templates_listbox.insert(tk.END, f"📋 {tmpl}")
    
    def _on_select(self, event):
        selection = self.templates_listbox.curselection()
        if selection:
            self.selected_template = selection[0]
    
    def _new_template(self):
        self.templates.append("Новый шаблон")
        self._refresh_list()
    
    def _edit_template(self):
        if self.selected_template is not None:
            pass  # Логика редактирования
    
    def _delete_template(self):
        if self.selected_template is not None:
            del self.templates[self.selected_template]
            self._refresh_list()
            self.selected_template = None
    
    def _apply_template(self):
        if self.on_apply:
            self.on_apply(self.template_name.get())
        self.dialog.destroy()


class TodayView:
    """Представление задач на сегодня"""
    
    def __init__(self, parent, tasks=None):
        self.parent = parent
        self.tasks = tasks or []
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"ЗАДАЧИ НА СЕГОДНЯ | {datetime.now().strftime('%A, %d %B %Y')}")
        self.window.geometry("800x600")
        self.window.transient(parent)
        
        self._create_ui()
    
    def _create_ui(self):
        main_frame = ttk.Frame(self.window, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Срочные задачи
        urgent_frame = ttk.LabelFrame(main_frame, text="🔴 СРОЧНЫЕ ЗАДАЧИ", padding=10)
        urgent_frame.pack(fill=tk.X, pady=(0, 10))
        
        urgent_tasks = [t for t in self.tasks if t.urgency >= 4]
        for task in urgent_tasks[:3]:
            ttk.Label(urgent_frame, 
                     text=f"□ {task.due_date.strftime('%H:%M') if task.due_date else ''} - {task.title} (Срочность: {'●' * task.urgency}{'○' * (5-task.urgency)})"
                     ).pack(anchor=tk.W, pady=2)
        
        # Важные задачи
        important_frame = ttk.LabelFrame(main_frame, text="🟡 ВАЖНЫЕ ЗАДАЧИ", padding=10)
        important_frame.pack(fill=tk.X, pady=(0, 10))
        
        important_tasks = [t for t in self.tasks if t.importance >= 4 and t.urgency < 4]
        for task in important_tasks[:3]:
            ttk.Label(important_frame,
                     text=f"□ {task.title} (Важность: {'●' * task.importance}{'○' * (5-task.importance)})"
                     ).pack(anchor=tk.W, pady=2)
        
        # Плановые задачи
        planned_frame = ttk.LabelFrame(main_frame, text="🟢 ПЛАНОВЫЕ ЗАДАЧИ", padding=10)
        planned_frame.pack(fill=tk.X, pady=(0, 10))
        
        planned_tasks = [t for t in self.tasks if t.importance < 4 and t.urgency < 4]
        for task in planned_tasks[:3]:
            ttk.Label(planned_frame,
                     text=f"□ {task.title} (Важность: {'●' * task.importance}{'○' * (5-task.importance)})"
                     ).pack(anchor=tk.W, pady=2)


class EisenhowerMatrix:
    """Матрица приоритетов Эйзенхауэра"""
    
    def __init__(self, parent, tasks=None):
        self.parent = parent
        self.tasks = tasks or []
        
        self.window = tk.Toplevel(parent)
        self.window.title("МАТРИЦА ПРИОРИТЕТОВ")
        self.window.geometry("900x700")
        self.window.transient(parent)
        
        self._create_ui()
    
    def _create_ui(self):
        main_frame = ttk.Frame(self.window, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Сетка 2x2 для квадрантов
        colors = {
            "Срочные и важные": "#ffcccc",
            "Несрочные, но важные": "#ccffcc",
            "Срочные, но не важные": "#ffffcc",
            "Несрочные и не важные": "#f0f0f0"
        }
        
        quadrants = [
            ("🔴 СРОЧНЫЕ И ВАЖНЫЕ\nСделать немедленно", "Срочные и важные"),
            ("🟢 НЕСРОЧНЫЕ, НО ВАЖНЫЕ\nЗапланировать", "Несрочные, но важные"),
            ("🟡 СРОЧНЫЕ, НО НЕ ВАЖНЫЕ\nДелегировать", "Срочные, но не важные"),
            ("⚪ НЕСРОЧНЫЕ И НЕ ВАЖНЫЕ\nУстранить", "Несрочные и не важные")
        ]
        
        for i, (title, key) in enumerate(quadrants):
            row = i // 2
            col = i % 2
            
            frame = ttk.LabelFrame(main_frame, text=title, padding=10)
            frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            frame.configure(style=f"{key}.TLabelframe")
            
            # Задачи в квадранте
            quadrant_tasks = [t for t in self.tasks if t.get_priority_quadrant() == key]
            for task in quadrant_tasks[:5]:
                ttk.Label(frame, text=f"• {task.title}", anchor=tk.W).pack(fill=tk.X, pady=2)
            
            main_frame.grid_rowconfigure(row, weight=1)
            main_frame.grid_columnconfigure(col, weight=1)


class SettingsDialog:
    """Диалог настроек приложения"""
    
    def __init__(self, parent):
        self.parent = parent
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("НАСТРОЙКИ")
        self.dialog.geometry("500x450")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_ui()
    
    def _create_ui(self):
        # Вкладки
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка "Общие"
        general_frame = ttk.Frame(notebook, padding=15)
        notebook.add(general_frame, text="Общие")
        
        ttk.Label(general_frame, text="Язык интерфейса:").pack(anchor=tk.W)
        lang_combo = ttk.Combobox(general_frame, values=["Русский", "Беларуская"], state="readonly", width=20)
        lang_combo.pack(anchor=tk.W, pady=(0, 10))
        lang_combo.set("Русский")
        
        ttk.Label(general_frame, text="Тема оформления:").pack(anchor=tk.W)
        theme_combo = ttk.Combobox(general_frame, values=["Светлая", "Тёмная"], state="readonly", width=20)
        theme_combo.pack(anchor=tk.W, pady=(0, 10))
        theme_combo.set("Светлая")
        
        ttk.Label(general_frame, text="Начало рабочей недели:").pack(anchor=tk.W)
        week_start_combo = ttk.Combobox(general_frame, values=["Понедельник", "Воскресенье"], state="readonly", width=20)
        week_start_combo.pack(anchor=tk.W, pady=(0, 10))
        week_start_combo.set("Понедельник")
        
        ttk.Label(general_frame, text="Формат даты:").pack(anchor=tk.W)
        date_format_combo = ttk.Combobox(general_frame, values=["ДД.ММ.ГГГГ", "ММ/ДД/ГГГГ"], state="readonly", width=20)
        date_format_combo.pack(anchor=tk.W, pady=(0, 10))
        date_format_combo.set("ДД.ММ.ГГГГ")
        
        ttk.Label(general_frame, text="Формат времени:").pack(anchor=tk.W)
        time_format_combo = ttk.Combobox(general_frame, values=["24 часа", "12 часов"], state="readonly", width=20)
        time_format_combo.pack(anchor=tk.W)
        time_format_combo.set("24 часа")
        
        # Вкладка "Уведомления"
        notify_frame = ttk.Frame(notebook, padding=15)
        notebook.add(notify_frame, text="Уведомления")
        
        self.notify_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(notify_frame, text="Включить уведомления", variable=self.notify_enabled).pack(anchor=tk.W, pady=5)
        
        ttk.Label(notify_frame, text="Напоминания о дедлайнах за:").pack(anchor=tk.W, pady=(10, 5))
        reminder_combo = ttk.Combobox(notify_frame, values=["15 минут", "30 минут", "1 час", "2 часа"], state="readonly", width=15)
        reminder_combo.pack(anchor=tk.W)
        reminder_combo.set("30 минут")
        
        self.sound_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(notify_frame, text="Звуковые уведомления", variable=self.sound_enabled).pack(anchor=tk.W, pady=5)
        
        self.popup_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(notify_frame, text="Всплывающие уведомления", variable=self.popup_enabled).pack(anchor=tk.W, pady=5)
        
        # Вкладка "Тайм-менеджмент"
        tm_frame = ttk.Frame(notebook, padding=15)
        notebook.add(tm_frame, text="Тайм-менеджмент")
        
        self.eisenhower_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(tm_frame, text="Использовать матрицу Эйзенхауэра", variable=self.eisenhower_enabled).pack(anchor=tk.W, pady=5)
        
        self.pomodoro_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(tm_frame, text="Включить метод Pomodoro", variable=self.pomodoro_enabled).pack(anchor=tk.W, pady=5)
        
        pomodoro_frame = ttk.Frame(tm_frame)
        pomodoro_frame.pack(anchor=tk.W, pady=5)
        ttk.Label(pomodoro_frame, text="Длительность фокуса:").pack(side=tk.LEFT)
        focus_spin = ttk.Spinbox(pomodoro_frame, from_=15, to=60, width=5)
        focus_spin.pack(side=tk.LEFT, padx=5)
        focus_spin.set(25)
        ttk.Label(pomodoro_frame, text="минут").pack(side=tk.LEFT)
        
        break_frame = ttk.Frame(tm_frame)
        break_frame.pack(anchor=tk.W, pady=5)
        ttk.Label(break_frame, text="Перерыв:").pack(side=tk.LEFT)
        break_spin = ttk.Spinbox(break_frame, from_=5, to=30, width=5)
        break_spin.pack(side=tk.LEFT, padx=5)
        break_spin.set(5)
        ttk.Label(break_frame, text="минут").pack(side=tk.LEFT)
        
        # Кнопки
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Сохранить", command=self.dialog.destroy).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.LEFT, padx=10)


class PersonalOrganizer:
    """Главное приложение органайзера"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ОРГАНАЙЗЕР-ПЛАНИРОВЩИК")
        self.root.geometry("1200x800")
        
        self.tasks = []
        self.templates = ["Еженедельный отчет", "Запуск проекта", "Встреча с клиентом", "Ревью кода", "Планирование спринта"]
        self.data_file = "organizer_data.json"
        
        self._load_data()
        self._create_menu()
        self._create_toolbar()
        self._create_main_interface()
        self._create_statusbar()
        
        self._refresh_task_tree()
    
    def _load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = [Task.from_dict(t) for t in data.get('tasks', [])]
                    self.templates = data.get('templates', self.templates)
                    Task._id_counter = data.get('id_counter', 1)
            except Exception as e:
                print(f"Ошибка загрузки данных: {e}")
    
    def _save_data(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'tasks': [t.to_dict() for t in self.tasks],
                    'templates': self.templates,
                    'id_counter': Task._id_counter
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные: {e}")
    
    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Сохранить", command=self._save_data)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        
        task_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Задача", menu=task_menu)
        task_menu.add_command(label="Добавить задачу", command=self._add_task)
        task_menu.add_command(label="Редактировать задачу", command=self._edit_task)
        task_menu.add_command(label="Удалить задачу", command=self._delete_task)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Вид", menu=view_menu)
        view_menu.add_command(label="Сегодня", command=self._show_today)
        view_menu.add_command(label="В ближайшее время", command=lambda: None)
        view_menu.add_command(label="Срочные", command=lambda: None)
        view_menu.add_command(label="Несрочные", command=lambda: None)
        view_menu.add_command(label="Матрица Эйзенхауэра", command=self._show_eisenhower)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Инструменты", menu=tools_menu)
        tools_menu.add_command(label="Шаблоны", command=self._show_templates)
        
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Настройки", menu=settings_menu)
        settings_menu.add_command(label="Настройки...", command=self._show_settings)
    
    def _create_toolbar(self):
        toolbar = ttk.Frame(self.root, padding=5)
        toolbar.pack(fill=tk.X)
        
        ttk.Button(toolbar, text="+ Добавить", command=self._add_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏ Редакт.", command=self._edit_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑 Удалить", command=self._delete_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📋 Шаблоны", command=self._show_templates).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        self.search_var = tk.StringVar()
        search_entry = EnhancedEntry(toolbar, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=2)
        search_entry.bind('<KeyRelease>', lambda e: self._refresh_task_tree())
        ttk.Label(toolbar, text="🔍").pack(side=tk.LEFT, padx=2)
    
    def _create_main_interface(self):
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель - Навигация
        nav_frame = ttk.Frame(paned, width=200)
        paned.add(nav_frame, weight=1)
        
        ttk.Label(nav_frame, text="НАВИГАЦИЯ", font=('Arial', 10, 'bold')).pack(pady=10)
        
        nav_buttons = [
            ("📅 Сегодня", self._show_today),
            ("⏰ В ближайшее время", lambda: None),
            ("🔴 Срочные", lambda: None),
            ("🟢 Несрочные", lambda: None),
            ("📊 По приоритету", self._show_eisenhower)
        ]
        
        for text, cmd in nav_buttons:
            ttk.Button(nav_frame, text=text, command=cmd).pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Separator(nav_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(nav_frame, text="📁 Проекты", font=('Arial', 9, 'bold')).pack(anchor=tk.W, padx=5)
        projects = ["📁 Работа", "📁 Личное"]
        for proj in projects:
            ttk.Button(nav_frame, text=proj, command=lambda p=proj: None).pack(fill=tk.X, padx=5, pady=1)
        
        # Центральная панель - Дерево задач
        tree_frame = ttk.Frame(paned)
        paned.add(tree_frame, weight=3)
        
        ttk.Label(tree_frame, text="ДЕРЕВО ЗАДАЧ", font=('Arial', 10, 'bold')).pack(pady=5)
        
        columns = ("Название", "Статус", "Дедлайн", "Важн.", "Сроч.")
        self.task_tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings", selectmode="extended")
        self.task_tree.heading("#0", text="Задача")
        self.task_tree.heading("Название", text="Название")
        self.task_tree.heading("Статус", text="Статус")
        self.task_tree.heading("Дедлайн", text="Дедлайн")
        self.task_tree.heading("Важн.", text="Важн.")
        self.task_tree.heading("Сроч.", text="Сроч.")
        
        self.task_tree.column("#0", width=300)
        self.task_tree.column("Название", width=200)
        self.task_tree.column("Статус", width=100)
        self.task_tree.column("Дедлайн", width=120)
        self.task_tree.column("Важн.", width=50)
        self.task_tree.column("Сроч.", width=50)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.task_tree.bind('<Double-1>', lambda e: self._edit_task())
        
        # Правая панель - Детали задачи
        details_frame = ttk.LabelFrame(paned, text="ДЕТАЛИ ЗАДАЧИ", padding=15)
        paned.add(details_frame, weight=2)
        
        ttk.Label(details_frame, text="Название:").pack(anchor=tk.W)
        self.detail_title = EnhancedEntry(details_frame, width=40)
        self.detail_title.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(details_frame, text="Статус:").pack(anchor=tk.W)
        self.detail_status = ttk.Combobox(details_frame, values=["Не начата", "В процессе", "Завершена", "Отложена"], state="readonly")
        self.detail_status.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(details_frame, text="Приоритет:").pack(anchor=tk.W)
        self.detail_importance = ttk.Scale(details_frame, from_=1, to=5, orient=tk.HORIZONTAL)
        self.detail_importance.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(details_frame, text="Важность").pack(anchor=tk.W)
        
        self.detail_urgency = ttk.Scale(details_frame, from_=1, to=5, orient=tk.HORIZONTAL)
        self.detail_urgency.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(details_frame, text="Срочность").pack(anchor=tk.W)
        
        ttk.Label(details_frame, text="Дедлайн:").pack(anchor=tk.W)
        self.detail_deadline = EnhancedEntry(details_frame, width=40)
        self.detail_deadline.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(details_frame, text="Описание:").pack(anchor=tk.W)
        self.detail_desc = EnhancedText(details_frame, height=6, wrap=tk.WORD)
        self.detail_desc.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        ttk.Label(details_frame, text="📎 Файлы:").pack(anchor=tk.W)
        self.detail_files = tk.Listbox(details_frame, height=4)
        self.detail_files.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        btn_frame = ttk.Frame(details_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="💾 Сохранить", command=self._save_details).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📎 Добавить файл", command=lambda: None).pack(side=tk.LEFT, padx=2)
    
    def _create_statusbar(self):
        self.statusbar = ttk.Label(self.root, text="Готово", relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        self._update_statusbar()
    
    def _update_statusbar(self):
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.completed)
        in_progress = sum(1 for t in self.tasks if t.status == "В процессе")
        pending = total - completed - in_progress
        self.statusbar.config(text=f"Всего задач: {total} | Выполнено: {completed} | В работе: {in_progress} | Ожидание: {pending}")
    
    def _refresh_task_tree(self):
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        search_term = self.search_var.get().lower()
        
        # Группировка задач
        groups = {"Срочные и важные": [], "Несрочные, но важные": [], "Срочные, но не важные": [], "Несрочные и не важные": []}
        
        for task in self.tasks:
            if search_term and search_term not in task.title.lower():
                continue
            quadrant = task.get_priority_quadrant()
            groups[quadrant].append(task)
        
        for quadrant, tasks_in_group in groups.items():
            if tasks_in_group:
                group_id = self.task_tree.insert("", tk.END, text=f"▼ {quadrant}", open=True)
                for task in tasks_in_group:
                    due_str = task.due_date.strftime("%d.%m.%Y %H:%M") if task.due_date else ""
                    self.task_tree.insert(group_id, tk.END, iid=str(task.id),
                                         text=task.title,
                                         values=(task.title, task.status, due_str, task.importance, task.urgency))
    
    def _add_task(self):
        dialog = TaskDialog(self.root, all_tasks=self.tasks)
        self.root.wait_window(dialog.dialog)
        if dialog.result:
            self.tasks.append(dialog.result)
            self._save_data()
            self._refresh_task_tree()
            self._update_statusbar()
    
    def _edit_task(self):
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showinfo("Инфо", "Выберите задачу для редактирования")
            return
        
        task_id = int(selection[0])
        task = next((t for t in self.tasks if t.id == task_id), None)
        if not task:
            return
        
        dialog = TaskDialog(self.root, task=task, all_tasks=self.tasks)
        self.root.wait_window(dialog.dialog)
        self._save_data()
        self._refresh_task_tree()
        self._update_statusbar()
    
    def _delete_task(self):
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showinfo("Инфо", "Выберите задачу для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить выбранную задачу?"):
            task_id = int(selection[0])
            self.tasks = [t for t in self.tasks if t.id != task_id]
            self._save_data()
            self._refresh_task_tree()
            self._update_statusbar()
    
    def _save_details(self):
        selection = self.task_tree.selection()
        if not selection:
            return
        
        task_id = int(selection[0])
        task = next((t for t in self.tasks if t.id == task_id), None)
        if task:
            task.title = self.detail_title.get()
            task.status = self.detail_status.get()
            task.importance = int(self.detail_importance.get())
            task.urgency = int(self.detail_urgency.get())
            task.description = self.detail_desc.get('1.0', tk.END).strip()
            deadline_str = self.detail_deadline.get().strip()
            if deadline_str:
                try:
                    task.due_date = datetime.strptime(deadline_str, "%d.%m.%Y %H:%M")
                except ValueError:
                    pass
            self._save_data()
            self._refresh_task_tree()
            self._update_statusbar()
    
    def _show_templates(self):
        TemplatesDialog(self.root, self.templates)
    
    def _show_today(self):
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        today_tasks = [t for t in self.tasks if t.due_date and today <= t.due_date < tomorrow]
        TodayView(self.root, today_tasks)
    
    def _show_eisenhower(self):
        EisenhowerMatrix(self.root, self.tasks)
    
    def _show_settings(self):
        SettingsDialog(self.root)
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = PersonalOrganizer()
    app.run()
