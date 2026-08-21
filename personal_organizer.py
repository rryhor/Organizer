import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from datetime import datetime
import json
import os
import threading
import time

# Файл для хранения данных
DATA_FILE = "organizer_data.json"

class Task:
    def __init__(self, title, task_type, due_date, description="", completed=False):
        self.id = int(time.time() * 1000)  # Уникальный ID
        self.title = title
        self.task_type = task_type
        self.due_date = due_date
        self.description = description
        self.completed = completed
        self.notified = False
        self.subtasks = []  # Список подзаданий

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "task_type": self.task_type,
            "due_date": self.due_date,
            "description": self.description,
            "completed": self.completed,
            "notified": self.notified,
            "subtasks": self.subtasks
        }

    @staticmethod
    def from_dict(data):
        task = Task(
            data["title"],
            data["task_type"],
            data["due_date"],
            data.get("description", ""),
            data.get("completed", False)
        )
        task.id = data["id"]
        task.notified = data.get("notified", False)
        task.subtasks = data.get("subtasks", [])
        return task

class SubtaskEditorFrame(ttk.Frame):
    """Фрейм для редактирования списка подзаданий с комментариями"""
    def __init__(self, parent, subtasks_data=None):
        super().__init__(parent)
        self.subtasks_data = subtasks_data or []
        
        ttk.Label(self, text="Подзадания:").pack(anchor=tk.W, pady=(10, 5))
        
        # Контейнер для списка подзаданий
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Название", "Комментарий", "Выполнено")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=6)
        self.tree.heading("Название", text="Название")
        self.tree.column("Название", width=200, anchor=tk.W)
        self.tree.heading("Комментарий", text="Комментарий")
        self.tree.column("Комментарий", width=150, anchor=tk.W)
        self.tree.heading("Выполнено", text="✓")
        self.tree.column("Выполнено", width=40, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопки управления
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(btn_frame, text="+ Добавить", command=self.add_subtask).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_subtask).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Изменить", command=self.edit_subtask).pack(side=tk.LEFT, padx=2)
        
        # Заполняем данными
        self.refresh_list()
    
    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for sub in self.subtasks_data:
            status = "✓" if sub.get('completed', False) else ""
            comment = sub.get('comment', '')
            self.tree.insert("", tk.END, values=(sub['title'], comment, status))
    
    def add_subtask(self):
        dialog = SubtaskEditDialog(self, None)
        self.wait_window(dialog)
        if dialog.result:
            self.subtasks_data.append(dialog.result)
            self.refresh_list()
    
    def edit_subtask(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите подзадание для редактирования", parent=self)
            return
        item = self.tree.item(selection[0])
        title = item['values'][0]
        comment = item['values'][1]
        completed = item['values'][2] == "✓"
        
        # Находим индекс
        idx = None
        for i, sub in enumerate(self.subtasks_data):
            if sub['title'] == title:
                idx = i
                break
        
        if idx is not None:
            dialog = SubtaskEditDialog(self, {'title': title, 'comment': comment, 'completed': completed})
            self.wait_window(dialog)
            if dialog.result:
                self.subtasks_data[idx] = dialog.result
                self.refresh_list()
    
    def delete_subtask(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите подзадание для удаления", parent=self)
            return
        item = self.tree.item(selection[0])
        title = item['values'][0]
        
        if messagebox.askyesno("Подтверждение", "Удалить это подзадание?", parent=self):
            self.subtasks_data = [s for s in self.subtasks_data if s['title'] != title]
            self.refresh_list()
    
    def get_subtasks(self):
        return self.subtasks_data


class SubtaskEditDialog(tk.Toplevel):
    """Диалог добавления/редактирования подзадания с комментарием"""
    def __init__(self, parent, edit_data=None):
        super().__init__(parent)
        self.title("Добавить подзадание" if not edit_data else "Редактировать подзадание")
        self.geometry("400x250")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.result = None
        
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_reqwidth()) / 2
        y = (self.winfo_screenheight() - self.winfo_reqheight()) / 2
        self.geometry(f"+{int(x)}+{int(y)}")
        
        ttk.Label(self, text="Название:").pack(pady=(15, 0))
        self.title_entry = ttk.Entry(self, width=45)
        self.title_entry.pack(pady=5)
        if edit_data:
            self.title_entry.insert(0, edit_data['title'])
        self.title_entry.focus()
        
        ttk.Label(self, text="Комментарий:").pack(pady=(10, 0))
        self.comment_text = tk.Text(self, height=5, width=45)
        self.comment_text.pack(pady=5)
        if edit_data and edit_data.get('comment'):
            self.comment_text.insert("1.0", edit_data['comment'])
        
        ttk.Label(self, text="Выполнено:").pack(pady=(10, 0))
        self.completed_var = tk.BooleanVar(value=edit_data.get('completed', False) if edit_data else False)
        ttk.Checkbutton(self, text="Отметить как выполненное", variable=self.completed_var).pack(pady=5)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=15)
        
        ttk.Button(btn_frame, text="Сохранить", command=self.on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=self.on_cancel).pack(side=tk.LEFT, padx=10)
    
    def on_ok(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Внимание", "Введите название подзадания!", parent=self)
            return
        
        self.result = {
            "id": int(time.time() * 1000),
            "title": title,
            "comment": self.comment_text.get("1.0", tk.END).strip(),
            "completed": self.completed_var.get()
        }
        self.destroy()
    
    def on_cancel(self):
        self.destroy()


class AddTaskDialog(tk.Toplevel):
    def __init__(self, parent, edit_task=None):
        super().__init__(parent)
        self.title("Добавить новое задание" if not edit_task else "Редактировать задание")
        self.geometry("500x650")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.result = None
        
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_reqwidth()) / 2
        y = (self.winfo_screenheight() - self.winfo_reqheight()) / 2
        self.geometry(f"+{int(x)}+{int(y)}")

        # Тип задачи
        ttk.Label(self, text="Тип задания:").pack(pady=(10, 0))
        type_val = edit_task.task_type if edit_task else "Встреча"
        self.type_var = tk.StringVar(value=type_val)
        type_combo = ttk.Combobox(self, textvariable=self.type_var, values=["Встреча", "Мероприятие", "Документы", "Срок сдачи"], state="readonly", width=50)
        type_combo.pack(pady=5)

        # Название
        ttk.Label(self, text="Название:").pack(pady=(10, 0))
        self.title_entry = ttk.Entry(self, width=50)
        self.title_entry.pack(pady=5)
        if edit_task:
            self.title_entry.insert(0, edit_task.title)
        self.title_entry.focus()

        # Описание
        ttk.Label(self, text="Описание (детали):").pack(pady=(10, 0))
        self.desc_text = tk.Text(self, height=4, width=50)
        self.desc_text.pack(pady=5)
        if edit_task and edit_task.description:
            self.desc_text.insert("1.0", edit_task.description)

        # Дата и Время (Календарь)
        ttk.Label(self, text="Дата и время выполнения:").pack(pady=(10, 0))
        
        cal_frame = ttk.Frame(self)
        cal_frame.pack(pady=5)

        self.calendar = Calendar(cal_frame, selectmode='day', date_pattern='yyyy-mm-dd', locale='ru_RU')
        self.calendar.pack(padx=10, pady=5)

        # Выбор времени
        time_frame = ttk.Frame(self)
        time_frame.pack(pady=5)
        
        ttk.Label(time_frame, text="Часы:").pack(side=tk.LEFT, padx=5)
        self.hour_spin = ttk.Spinbox(time_frame, from_=0, to=23, width=3, format='%02.0f')
        self.hour_spin.set(datetime.now().strftime('%H'))
        self.hour_spin.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        
        ttk.Label(time_frame, text="Минуты:").pack(side=tk.LEFT, padx=5)
        self.min_spin = ttk.Spinbox(time_frame, from_=0, to=59, width=3, format='%02.0f')
        self.min_spin.set('00')
        self.min_spin.pack(side=tk.LEFT, padx=2)

        if edit_task:
            try:
                dt = datetime.strptime(edit_task.due_date, "%Y-%m-%d %H:%M")
                self.calendar.selection_clear()
                self.calendar.cale.selection_set(dt.date())
                self.hour_spin.set(dt.strftime('%H'))
                self.min_spin.set(dt.strftime('%M'))
            except Exception:
                pass
        
        # Подзадания
        subtasks_data = []
        if edit_task and edit_task.subtasks:
            subtasks_data = edit_task.subtasks.copy()
        
        self.subtask_editor = SubtaskEditorFrame(self, subtasks_data)
        self.subtask_editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=15)

        ttk.Button(btn_frame, text="Сохранить", command=self.on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=self.on_cancel).pack(side=tk.LEFT, padx=10)

    def on_ok(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Внимание", "Введите название задания!", parent=self)
            return

        date_str = self.calendar.get_date()
        
        try:
            hour = int(self.hour_spin.get())
            minute = int(self.min_spin.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат времени", parent=self)
            return

        full_datetime = f"{date_str} {hour:02d}:{minute:02d}"
        description = self.desc_text.get("1.0", tk.END).strip()
        
        self.result = {
            "title": title,
            "type": self.type_var.get(),
            "due_date": full_datetime,
            "description": description,
            "subtasks": self.subtask_editor.get_subtasks()
        }
        self.destroy()

    def on_cancel(self):
        self.destroy()

class PersonalOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Персональный Органайзер")
        self.root.geometry("900x600")
        
        self.tasks = []
        self.load_data()
        
        menubar = tk.Menu(root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Добавить задание", command=self.open_add_task)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)
        root.config(menu=menubar)

        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(control_frame, text="+ Добавить задание", command=self.open_add_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Удалить выбранное", command=self.delete_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Изменить", command=self.edit_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Выполнено/Нет", command=self.toggle_complete).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Поиск:").pack(side=tk.LEFT, padx=(20, 5))
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add('write', lambda name, index, mode: self.refresh_list())
        filter_entry = ttk.Entry(control_frame, textvariable=self.filter_var, width=20)
        filter_entry.pack(side=tk.LEFT)

        columns = ("Тип", "Название", "Срок", "Статус")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("Тип", text="Тип")
        self.tree.column("Тип", width=100, anchor=tk.CENTER)
        self.tree.heading("Название", text="Название")
        self.tree.column("Название", width=300, anchor=tk.W)
        self.tree.heading("Срок", text="Срок выполнения")
        self.tree.column("Срок", width=150, anchor=tk.CENTER)
        self.tree.heading("Статус", text="Статус")
        self.tree.column("Статус", width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        details_frame = ttk.LabelFrame(main_frame, text="Детали задачи", padding="10")
        details_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.details_text = tk.Text(details_frame, height=8, width=50, wrap=tk.WORD)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        # Добавляем поддержку Ctrl+C и Ctrl+V для деталей
        self.details_text.bind("<Control-c>", lambda e: self.copy_to_clipboard(self.details_text.get("sel.first", "sel.last")))
        self.details_text.bind("<Control-v>", lambda e: self.paste_from_clipboard(self.details_text))
        
        subtasks_frame = ttk.LabelFrame(main_frame, text="Подзадания (дерево)", padding="10")
        subtasks_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Используем Treeview с иерархией для отображения подзаданий с комментариями
        columns = ("Название", "Комментарий", "Выполнено")
        self.subtasks_tree = ttk.Treeview(subtasks_frame, columns=columns, show="headings", selectmode="browse", height=6)
        self.subtasks_tree.heading("Название", text="Название")
        self.subtasks_tree.column("Название", width=250, anchor=tk.W)
        self.subtasks_tree.heading("Комментарий", text="Комментарий")
        self.subtasks_tree.column("Комментарий", width=200, anchor=tk.W)
        self.subtasks_tree.heading("Выполнено", text="✓")
        self.subtasks_tree.column("Выполнено", width=40, anchor=tk.CENTER)
        
        subtasks_scrollbar = ttk.Scrollbar(subtasks_frame, orient=tk.VERTICAL, command=self.subtasks_tree.yview)
        self.subtasks_tree.configure(yscrollcommand=subtasks_scrollbar.set)
        
        self.subtasks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        subtasks_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        subtasks_btn_frame = ttk.Frame(subtasks_frame)
        subtasks_btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(subtasks_btn_frame, text="Добавить подзадание", command=self.add_subtask).pack(side=tk.LEFT, padx=5)
        ttk.Button(subtasks_btn_frame, text="Удалить", command=self.delete_subtask).pack(side=tk.LEFT, padx=5)
        ttk.Button(subtasks_btn_frame, text="Изменить", command=self.edit_subtask).pack(side=tk.LEFT, padx=5)
        ttk.Button(subtasks_btn_frame, text="Выполнено/Нет", command=self.toggle_subtask_complete).pack(side=tk.LEFT, padx=5)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", self.edit_task)

        self.running = True
        self.notify_thread = threading.Thread(target=self.check_reminders, daemon=True)
        self.notify_thread.start()

        self.refresh_list()

    def open_add_task(self):
        dialog = AddTaskDialog(self.root)
        self.root.wait_window(dialog)
        
        if dialog.result:
            res = dialog.result
            new_task = Task(
                title=res["title"],
                task_type=res["type"],
                due_date=res["due_date"],
                description=res["description"]
            )
            new_task.subtasks = res.get("subtasks", [])
            self.tasks.append(new_task)
            self.save_data()
            self.refresh_list()

    def edit_task(self, event=None):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите задачу для редактирования")
            return
        
        selected_item = self.tree.item(selection[0])
        task_title = selected_item['values'][1]  # Название теперь второй колонке (после Типа)
        task = next((t for t in self.tasks if t.title == task_title and t.due_date == selected_item['values'][2]), None)
        if not task:
            return

        dialog = AddTaskDialog(self.root, edit_task=task)
        self.root.wait_window(dialog)
        
        if dialog.result:
            res = dialog.result
            task.title = res["title"]
            task.task_type = res["type"]
            task.due_date = res["due_date"]
            task.description = res["description"]
            task.subtasks = res.get("subtasks", [])
            self.save_data()
            self.refresh_list()

    def delete_task(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите задачу для удаления")
            return
        
        selected_item = self.tree.item(selection[0])
        task_title = selected_item['values'][1]
        task_due = selected_item['values'][2]
        
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту задачу?"):
            self.tasks = [t for t in self.tasks if not (t.title == task_title and t.due_date == task_due)]
            self.save_data()
            self.refresh_list()

    def toggle_complete(self):
        selection = self.tree.selection()
        if not selection:
            return
        
        selected_item = self.tree.item(selection[0])
        task_title = selected_item['values'][1]
        task_due = selected_item['values'][2]
        task = next((t for t in self.tasks if t.title == task_title and t.due_date == task_due), None)
        if task:
            task.completed = not task.completed
            self.save_data()
            self.refresh_list()

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            self.details_text.delete("1.0", tk.END)
            self.details_text.insert(tk.END, "Выберите задачу для просмотра деталей")
            self.subtasks_tree.delete(*self.subtasks_tree.get_children())
            return
        
        selected_item = self.tree.item(selection[0])
        task_title = selected_item['values'][1]
        task_due = selected_item['values'][2]
        task = next((t for t in self.tasks if t.title == task_title and t.due_date == task_due), None)
        
        if task:
            status = "Выполнено" if task.completed else "В ожидании"
            text = (f"Задача: {task.title}\n"
                    f"Тип: {task.task_type}\n"
                    f"Срок: {task.due_date}\n"
                    f"Статус: {status}\n"
                    f"Описание: {task.description if task.description else 'Нет'}")
            self.details_text.delete("1.0", tk.END)
            self.details_text.insert(tk.END, text)
            
            # Обновляем список подзаданий
            self.refresh_subtasks_list(task)

    def refresh_subtasks_list(self, task):
        for item in self.subtasks_tree.get_children():
            self.subtasks_tree.delete(item)
        
        for subtask in task.subtasks:
            status = "✓" if subtask.get('completed', False) else ""
            comment = subtask.get('comment', '')
            self.subtasks_tree.insert("", tk.END, values=(subtask['title'], comment, status))

    def add_subtask(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите задачу для добавления подзадания")
            return
        
        selected_item = self.tree.item(selection[0])
        task_title = selected_item['values'][1]
        task_due = selected_item['values'][2]
        task = next((t for t in self.tasks if t.title == task_title and t.due_date == task_due), None)
        if not task:
            return
        
        dialog = SubtaskEditDialog(self.root, None)
        self.root.wait_window(dialog)
        
        if dialog.result:
            task.subtasks.append(dialog.result)
            self.save_data()
            self.refresh_list()
            self.on_select(None)  # Обновить панель деталей

    def edit_subtask(self):
        selection = self.subtasks_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите подзадание для редактирования")
            return
        
        tree_selection = self.tree.selection()
        if not tree_selection:
            return
        
        selected_main_item = self.tree.item(tree_selection[0])
        task_title = selected_main_item['values'][1]
        task_due = selected_main_item['values'][2]
        task = next((t for t in self.tasks if t.title == task_title and t.due_date == task_due), None)
        if not task:
            return
        
        selected_item = self.subtasks_tree.item(selection[0])
        subtask_title = selected_item['values'][0]
        subtask_comment = selected_item['values'][1]
        subtask_completed = selected_item['values'][2] == "✓"
        
        # Находим подзадание
        subtask_data = None
        for sub in task.subtasks:
            if sub['title'] == subtask_title:
                subtask_data = {'title': subtask_title, 'comment': subtask_comment, 'completed': subtask_completed}
                break
        
        if subtask_data:
            dialog = SubtaskEditDialog(self.root, subtask_data)
            self.root.wait_window(dialog)
            if dialog.result:
                # Находим индекс и заменяем
                for i, sub in enumerate(task.subtasks):
                    if sub['title'] == subtask_title:
                        task.subtasks[i] = dialog.result
                        break
                self.save_data()
                self.refresh_list()
                self.on_select(None)

    def delete_subtask(self):
        selection = self.subtasks_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите подзадание для удаления")
            return
        
        tree_selection = self.tree.selection()
        if not tree_selection:
            return
        
        selected_main_item = self.tree.item(tree_selection[0])
        task_title = selected_main_item['values'][1]
        task_due = selected_main_item['values'][2]
        task = next((t for t in self.tasks if t.title == task_title and t.due_date == task_due), None)
        if not task:
            return
        
        selected_item = self.subtasks_tree.item(selection[0])
        subtask_title = selected_item['values'][0]
        
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить это подзадание?"):
            task.subtasks = [s for s in task.subtasks if s['title'] != subtask_title]
            self.save_data()
            self.refresh_list()
            self.on_select(None)

    def toggle_subtask_complete(self):
        selection = self.subtasks_tree.selection()
        if not selection:
            return
        
        tree_selection = self.tree.selection()
        if not tree_selection:
            return
        
        selected_main_item = self.tree.item(tree_selection[0])
        task_title = selected_main_item['values'][1]
        task_due = selected_main_item['values'][2]
        task = next((t for t in self.tasks if t.title == task_title and t.due_date == task_due), None)
        if not task:
            return
        
        selected_item = self.subtasks_tree.item(selection[0])
        subtask_title = selected_item['values'][0]
        
        for subtask in task.subtasks:
            if subtask['title'] == subtask_title:
                subtask['completed'] = not subtask.get('completed', False)
                break
        
        self.save_data()
        self.refresh_list()
        self.on_select(None)

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        search_term = self.filter_var.get()
        sorted_tasks = sorted(self.tasks, key=lambda x: x.due_date)

        for task in sorted_tasks:
            if not search_term or search_term.lower() in task.title.lower() or search_term.lower() in task.description.lower():
                status = "Выполнено" if task.completed else "Ожидание"
                
                self.tree.insert("", tk.END, values=(
                    task.task_type,
                    task.title,
                    task.due_date,
                    status
                ), tags=('completed' if task.completed else 'active',))
        
        self.tree.tag_configure('completed', background='#e0ffe0')
        self.tree.tag_configure('active', background='white')

    def check_reminders(self):
        while self.running:
            now = datetime.now()
            for task in self.tasks:
                if task.completed or task.notified:
                    continue
                
                try:
                    due_dt = datetime.strptime(task.due_date, "%Y-%m-%d %H:%M")
                    diff = (due_dt - now).total_seconds()
                    
                    if 0 < diff <= 3600:
                        self.root.after(0, lambda t=task: self.show_notification(t))
                        task.notified = True
                        self.save_data()
                except Exception:
                    pass
            
            time.sleep(60)

    def show_notification(self, task):
        messagebox.showwarning("Напоминание", 
                               f"Скоро срок выполнения задачи!\n\n"
                               f"{task.title}\n"
                               f"Срок: {task.due_date}", 
                               parent=self.root)

    def save_data(self):
        data = [t.to_dict() for t in self.tasks]
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.tasks = [Task.from_dict(item) for item in data]
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            self.tasks = []

    def copy_to_clipboard(self, text):
        """Копирование текста в буфер обмена"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
    
    def paste_from_clipboard(self, widget):
        """Вставка текста из буфера обмена"""
        try:
            text = self.root.clipboard_get()
            widget.insert(tk.INSERT, text)
        except tk.TclError:
            pass  # Буфер обмена пуст или не содержит текст


if __name__ == "__main__":
    root = tk.Tk()
    app = PersonalOrganizer(root)
    root.protocol("WM_DELETE_WINDOW", lambda: setattr(app, 'running', False) or root.destroy())
    root.mainloop()
