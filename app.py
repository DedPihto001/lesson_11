"""Tkinter interface for managing users, tables, and bookings."""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Any, Callable

import psycopg2

import backend


def _display_datetime(value: Any) -> str:
    return value.isoformat(sep=" ", timespec="minutes") if value else ""


class BookingApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Restaurant Booking Manager")
        self.geometry("1120x650")
        self.minsize(900, 500)
        try:
            backend.init_db()
        except (psycopg2.Error, ValueError) as exc:
            messagebox.showerror("Ошибка подключения к базе данных", str(exc), parent=self)
            self.destroy()
            raise SystemExit(1) from exc
        self.user_choices: dict[str, int] = {}
        self.table_choices: dict[str, int] = {}

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.user_tab = ttk.Frame(notebook, padding=10)
        self.table_tab = ttk.Frame(notebook, padding=10)
        self.booking_tab = ttk.Frame(notebook, padding=10)
        notebook.add(self.user_tab, text="Пользователи")
        notebook.add(self.table_tab, text="Столы")
        notebook.add(self.booking_tab, text="Бронирования")

        self._build_users_tab()
        self._build_tables_tab()
        self._build_bookings_tab()
        self.refresh_all()

    def _tree(
        self,
        parent: ttk.Frame,
        columns: tuple[str, ...],
        headings: dict[str, str],
    ) -> ttk.Treeview:
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True, pady=(0, 10))
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=12)
        for column in columns:
            tree.heading(column, text=headings.get(column, column))
            tree.column(column, width=125, anchor="w")
        vertical = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        horizontal = ttk.Scrollbar(
            container, orient="horizontal", command=tree.xview
        )
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        tree.bind("<<TreeviewSelect>>", lambda _event: self._on_tree_select(tree))
        return tree

    def _form_entry(
        self, parent: ttk.Frame, label: str, row: int
    ) -> ttk.Entry:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=4, pady=3)
        entry = ttk.Entry(parent, width=30)
        entry.grid(row=row, column=1, sticky="ew", padx=4, pady=3)
        return entry

    def _build_users_tab(self) -> None:
        self.user_tree = self._tree(
            self.user_tab,
            ("id", "name", "email", "created_at"),
            {"id": "ID", "name": "Имя", "email": "Email", "created_at": "Создан"},
        )
        form = ttk.Frame(self.user_tab)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)
        self.user_name = self._form_entry(form, "Имя", 0)
        self.user_email = self._form_entry(form, "Email", 1)
        self._buttons(
            form,
            [
                ("Добавить", self._create_user),
                ("Обновить", self._update_user),
                ("Удалить", self._delete_user),
                ("Обновить список", self.refresh_users),
            ],
            2,
        )

    def _build_tables_tab(self) -> None:
        self.table_tree = self._tree(
            self.table_tab,
            ("id", "number", "seats", "description"),
            {
                "id": "ID",
                "number": "Номер",
                "seats": "Мест",
                "description": "Описание",
            },
        )
        form = ttk.Frame(self.table_tab)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)
        self.table_number = self._form_entry(form, "Номер стола", 0)
        self.table_seats = self._form_entry(form, "Количество мест", 1)
        self.table_description = self._form_entry(form, "Описание", 2)
        self._buttons(
            form,
            [
                ("Добавить", self._create_table),
                ("Обновить", self._update_table),
                ("Удалить", self._delete_table),
                ("Обновить список", self.refresh_tables),
            ],
            3,
        )

    def _build_bookings_tab(self) -> None:
        self.booking_tree = self._tree(
            self.booking_tab,
            (
                "id",
                "user_id",
                "user_name",
                "user_email",
                "table_id",
                "table_number",
                "booking_time",
                "duration_minutes",
                "created_at",
            ),
            {
                "id": "ID",
                "user_id": "ID пользователя",
                "user_name": "Имя",
                "user_email": "Email",
                "table_id": "ID стола",
                "table_number": "Номер стола",
                "booking_time": "Время",
                "duration_minutes": "Длительность, мин",
                "created_at": "Создано",
            },
        )
        form = ttk.Frame(self.booking_tab)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text="Пользователь").grid(
            row=0, column=0, sticky="w", padx=4, pady=3
        )
        self.booking_user = ttk.Combobox(form, state="readonly", width=28)
        self.booking_user.grid(row=0, column=1, sticky="ew", padx=4, pady=3)
        ttk.Label(form, text="Стол").grid(
            row=1, column=0, sticky="w", padx=4, pady=3
        )
        self.booking_table = ttk.Combobox(form, state="readonly", width=28)
        self.booking_table.grid(row=1, column=1, sticky="ew", padx=4, pady=3)
        self.booking_time = self._form_entry(form, "Дата/время (ГГГГ-ММ-ДД ЧЧ:ММ)", 2)
        self.booking_duration = self._form_entry(form, "Длительность, минут", 3)
        self.booking_duration.insert(0, "60")
        self._buttons(
            form,
            [
                ("Добавить", self._create_booking),
                ("Обновить", self._update_booking),
                ("Удалить", self._delete_booking),
                ("Обновить список", self.refresh_bookings),
                ("Проверить доступность", self._check_availability),
            ],
            4,
        )
        ttk.Label(
            form,
            text="Время вводится в формате 2026-12-31 18:30.",
        ).grid(row=5, column=0, columnspan=2, sticky="w", padx=4, pady=4)

    def _buttons(
        self,
        parent: ttk.Frame,
        buttons: list[tuple[str, Callable[[], None]]],
        row: int,
    ) -> None:
        for column, (label, command) in enumerate(buttons):
            ttk.Button(parent, text=label, command=command).grid(
                row=row, column=column, sticky="ew", padx=4, pady=8
            )

    def _selected_id(self, tree: ttk.Treeview) -> int:
        selected = tree.selection()
        if not selected:
            raise ValueError("Сначала выберите запись в списке.")
        return int(tree.item(selected[0], "values")[0])

    @staticmethod
    def _set_entry(entry: ttk.Entry, value: Any) -> None:
        entry.delete(0, tk.END)
        entry.insert(0, "" if value is None else str(value))

    def _on_tree_select(self, tree: ttk.Treeview) -> None:
        selected = tree.selection()
        if not selected:
            return
        values = tree.item(selected[0], "values")
        if tree is self.user_tree:
            self._set_entry(self.user_name, values[1])
            self._set_entry(self.user_email, values[2])
        elif tree is self.table_tree:
            self._set_entry(self.table_number, values[1])
            self._set_entry(self.table_seats, values[2])
            self._set_entry(self.table_description, values[3])
        else:
            self._choose_value(self.booking_user, values[1], self.user_choices)
            self._choose_value(self.booking_table, values[4], self.table_choices)
            self._set_entry(self.booking_time, values[6])
            self._set_entry(self.booking_duration, values[7])

    @staticmethod
    def _choose_value(
        widget: ttk.Combobox, identifier: str, choices: dict[str, int]
    ) -> None:
        for label, item_id in choices.items():
            if str(item_id) == str(identifier):
                widget.set(label)
                break

    def _handle(self, action: Callable[[], None]) -> None:
        try:
            action()
        except (psycopg2.Error, ValueError, KeyError, OverflowError) as exc:
            messagebox.showerror("Ошибка", str(exc), parent=self)

    def _booking_values(self) -> tuple[int, int, datetime, int]:
        if not self.booking_user.get() or not self.booking_table.get():
            raise ValueError("Выберите пользователя и стол.")
        user_id = self.user_choices[self.booking_user.get()]
        table_id = self.table_choices[self.booking_table.get()]
        booking_time = datetime.fromisoformat(self.booking_time.get().strip())
        duration = int(self.booking_duration.get())
        if duration <= 0:
            raise ValueError("Длительность должна быть больше нуля.")
        return user_id, table_id, booking_time, duration

    def _create_user(self) -> None:
        def create() -> None:
            backend.create_user(
                self.user_name.get().strip(), self.user_email.get().strip()
            )
            self.refresh_users()

        self._handle(create)

    def _update_user(self) -> None:
        def update() -> None:
            if not backend.update_user(
                self._selected_id(self.user_tree),
                self.user_name.get().strip(),
                self.user_email.get().strip(),
            ):
                raise ValueError("Пользователь не найден.")
            self.refresh_users()

        self._handle(update)

    def _delete_user(self) -> None:
        def delete() -> None:
            if not backend.delete_user(self._selected_id(self.user_tree)):
                raise ValueError("Пользователь не найден.")
            self.refresh_all()

        self._handle(delete)

    def _create_table(self) -> None:
        def create() -> None:
            backend.create_table(
                int(self.table_number.get()),
                int(self.table_seats.get()),
                self.table_description.get().strip() or None,
            )
            self.refresh_tables()

        self._handle(create)

    def _update_table(self) -> None:
        def update() -> None:
            if not backend.update_table(
                self._selected_id(self.table_tree),
                int(self.table_number.get()),
                int(self.table_seats.get()),
                self.table_description.get().strip() or None,
            ):
                raise ValueError("Стол не найден.")
            self.refresh_tables()

        self._handle(update)

    def _delete_table(self) -> None:
        def delete() -> None:
            if not backend.delete_table(self._selected_id(self.table_tree)):
                raise ValueError("Стол не найден.")
            self.refresh_all()

        self._handle(delete)

    def _create_booking(self) -> None:
        def create() -> None:
            user_id, table_id, booking_time, duration = self._booking_values()
            backend.create_booking(user_id, table_id, booking_time, duration)
            self.refresh_bookings()

        self._handle(create)

    def _update_booking(self) -> None:
        def update() -> None:
            user_id, table_id, booking_time, duration = self._booking_values()
            if not backend.update_booking(
                self._selected_id(self.booking_tree),
                user_id,
                table_id,
                booking_time,
                duration,
            ):
                raise ValueError("Бронирование не найдено.")
            self.refresh_bookings()

        self._handle(update)

    def _delete_booking(self) -> None:
        def delete() -> None:
            if not backend.delete_booking(self._selected_id(self.booking_tree)):
                raise ValueError("Бронирование не найдено.")
            self.refresh_bookings()

        self._handle(delete)

    def _check_availability(self) -> None:
        def check() -> None:
            _, table_id, booking_time, duration = self._booking_values()
            free = backend.check_table_availability(
                table_id, booking_time, duration
            )
            messagebox.showinfo(
                "Доступность",
                "Свободно" if free else "Занято",
                parent=self,
            )

        self._handle(check)

    def refresh_users(self) -> None:
        def refresh() -> None:
            users = backend.get_all_users()
            self._fill_tree(self.user_tree, users)
            self.user_choices = {
                f"{row['name']} (ID {row['id']})": int(row["id"]) for row in users
            }
            self.booking_user["values"] = list(self.user_choices)

        self._handle(refresh)

    def refresh_tables(self) -> None:
        def refresh() -> None:
            rows = backend.get_all_tables()
            self._fill_tree(self.table_tree, rows)
            self.table_choices = {
                f"Стол {row['number']} (ID {row['id']})": int(row["id"])
                for row in rows
            }
            self.booking_table["values"] = list(self.table_choices)

        self._handle(refresh)

    def refresh_bookings(self) -> None:
        self._handle(
            lambda: self._fill_tree(self.booking_tree, backend.get_all_bookings())
        )

    def refresh_all(self) -> None:
        def refresh() -> None:
            users = backend.get_all_users()
            self._fill_tree(self.user_tree, users)
            self.user_choices = {
                f"{row['name']} (ID {row['id']})": int(row["id"]) for row in users
            }
            self.booking_user["values"] = list(self.user_choices)
            self.refresh_tables()
            self._fill_tree(self.booking_tree, backend.get_all_bookings())

        self._handle(refresh)

    @staticmethod
    def _fill_tree(tree: ttk.Treeview, rows: list[dict[str, Any]]) -> None:
        tree.delete(*tree.get_children())
        for row in rows:
            values = []
            for column in tree["columns"]:
                value = row.get(column)
                if isinstance(value, datetime):
                    value = _display_datetime(value)
                values.append("" if value is None else value)
            tree.insert("", tk.END, values=values)


if __name__ == "__main__":
    BookingApp().mainloop()
