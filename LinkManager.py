import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import pyperclip
import webbrowser
import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        self.cursor = None
        self.connect_to_database()

    def connect_to_database(self):
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.cursor = self.conn.cursor()
            self.create_tables()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to connect to the database: {e}")

    def create_tables(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tabs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tab_id INTEGER,
                    title TEXT,
                    url TEXT,
                    FOREIGN KEY (tab_id) REFERENCES tabs(id)
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to create tables: {e}")

    def close_connection(self):
        if self.conn:
            self.conn.close()

class LinkManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Linky Pinky By Dr. Nee")
        self.geometry("800x600")
        self.resizable(True, True)
        self.configure(bg="#ffffff")  # Light blue background

        # Create database connection
        self.db_file = "links.db"
        self.db_manager = DatabaseManager(self.db_file)

        # Create top frame
        self.create_top_frame()

        # Create a notebook widget
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))

        # Load data
        self.load_data()

        # Bind right-click event for tabs
        self.notebook.bind("<Button-3>", self.tab_menu)

        # Bind window close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Set default tab to None
        self.default_tab = None

    def create_top_frame(self):
        top_frame = tk.Frame(self, bg="#ffffff")  # Lavender background
        top_frame.pack(side="top", fill="x", padx=10, pady=10)

        add_tab_button = tk.Button(top_frame, text="+", command=self.add_tab, bg="black", fg="white", font=("Arial", 12, "bold"), relief="raised", bd=1, width=2, height=1)
        add_tab_button.pack(side="left", padx=5)

        button_entry_frame = tk.Frame(top_frame, bg="#ffffff")
        button_entry_frame.pack(side="left", pady=5)

        paste_link_button = tk.Button(button_entry_frame, text="Paste Link", command=self.paste_link, bg="#D400A4", fg="white", font=("Arial", 12, "bold"), relief="raised", bd=1)
        paste_link_button.pack(side="left", padx=5)

        self.link_title_entry = tk.Entry(button_entry_frame, font=("Arial", 12), bg="white", width=30)
        self.link_title_entry.pack(side="left", padx=5)

    def load_data(self):
        try:
            self.db_manager.cursor.execute("SELECT id, name FROM tabs")
            tabs = self.db_manager.cursor.fetchall()

            for tab_id, tab_name in tabs:
                new_tab = Tab(self.notebook, self, tab_id)
                self.notebook.add(new_tab, text=tab_name)

                self.db_manager.cursor.execute("SELECT title, url FROM links WHERE tab_id = ?", (tab_id,))
                links = self.db_manager.cursor.fetchall()

                for title, url in links:
                    new_tab.add_link(title, url)

            # Set the first tab as the default tab
            self.default_tab = self.notebook.tabs()[0] if self.notebook.tabs() else None
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load data from the database: {e}")

    def add_tab(self):
        try:
            dialog = CustomDialog(self, "Enter tab name")
            dialog.geometry("+%d+%d" % ((self.winfo_rootx() + self.winfo_width() // 2) - 200, (self.winfo_rooty() + self.winfo_height() // 2) - 75))
            tab_name = dialog.show()
            if tab_name is not None:
                self.db_manager.cursor.execute("INSERT INTO tabs (name) VALUES (?)", (tab_name,))
                tab_id = self.db_manager.cursor.lastrowid
                new_tab = Tab(self.notebook, self, tab_id)
                self.notebook.add(new_tab, text=tab_name)
                self.notebook.select(new_tab)
                self.db_manager.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to add a new tab: {e}")

    def paste_link(self):
        try:
            selected_tab_widget = self.notebook.select()
            selected_tab = self.notebook.nametowidget(selected_tab_widget)
            link_title = self.link_title_entry.get()
            clipboard_text = pyperclip.paste()
            if selected_tab.check_duplicate_link(clipboard_text):
                messagebox.showwarning("Duplicate Link", "The link you are trying to paste already exists in this tab.")
            else:
                selected_tab.add_link(link_title, clipboard_text)
                self.link_title_entry.delete(0, "end")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while pasting link: {e}")

    def tab_menu(self, event):
        try:
            tab_menu = tk.Menu(self.notebook, tearoff=0)
            selected_tab_widget = self.notebook.select()
            selected_tab = self.notebook.nametowidget(selected_tab_widget)
            if selected_tab != self.default_tab:
                tab_menu.add_command(label="Rename Tab", command=lambda: self.rename_tab(event))
                tab_menu.add_command(label="Delete Tab", command=lambda: self.delete_tab(event))
            else:
                tab_menu.add_command(label="Rename Tab", command=lambda: self.rename_tab(event))
            tab_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while opening tab menu: {e}")

    def rename_tab(self, event):
        try:
            selected_tab = event.widget.select()
            selected_tab_widget = self.notebook.nametowidget(selected_tab)
            dialog = CustomDialog(self, "Enter new tab name")
            dialog.geometry("+%d+%d" % ((self.winfo_rootx() + self.winfo_width() // 2) - 200, (self.winfo_rooty() + self.winfo_height() // 2) - 75))
            new_name = dialog.show()
            if new_name is not None:
                self.db_manager.cursor.execute("UPDATE tabs SET name = ? WHERE id = ?", (new_name, selected_tab_widget.tab_id))
                self.db_manager.conn.commit()
                event.widget.tab(selected_tab, text=new_name)
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to rename tab: {e}")

    def delete_tab(self, event):
        try:
            selected_tab = event.widget.select()
            selected_tab_widget = self.notebook.nametowidget(selected_tab)
            if selected_tab_widget != self.default_tab:
                confirm = messagebox.askyesno("Delete Tab", "Are you sure you want to delete this tab?")
                if confirm:
                    self.db_manager.cursor.execute("DELETE FROM links WHERE tab_id = ?", (selected_tab_widget.tab_id,))
                    self.db_manager.cursor.execute("DELETE FROM tabs WHERE id = ?", (selected_tab_widget.tab_id,))
                    self.db_manager.conn.commit()
                    event.widget.forget(selected_tab)
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to delete tab: {e}")

    def on_close(self):
        try:
            self.db_manager.close_connection()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while closing the application: {e}")

class CustomDialog(tk.Toplevel):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)  # Disable maximize button
        self.configure(bg="#F0F8FF")  # Light blue background
        self.result = None  # Initialize result attribute

        input_frame = tk.Frame(self, bg="#E6E6FA")  # Lavender background
        input_frame.pack(padx=10, pady=10)

        self.input_box = tk.Entry(input_frame, font=("Arial", 12), bg="white", width=30)
        self.input_box.pack(side="left", padx=5)

        button_frame = tk.Frame(self, bg="#E6E6FA")
        button_frame.pack(padx=10, pady=(0, 10))

        ok_button = tk.Button(button_frame, text="OK", command=self.ok_clicked, bg="#348734", fg="white", font=("Arial", 10, "bold"), relief="raised", bd=1, width=6)
        ok_button.pack(side="left", padx=5)

        cancel_button = tk.Button(button_frame, text="Cancel", command=self.cancel_clicked, bg="#DC1902", fg="white", font=("Arial", 10, "bold"), relief="raised", bd=1, width=6)
        cancel_button.pack(side="left", padx=5)

        self.bind("<Return>", lambda event: self.ok_clicked())

    def ok_clicked(self):
        self.result = self.input_box.get()
        self.destroy()

    def cancel_clicked(self):
        self.result = None
        self.destroy()

    def show(self):
        self.grab_set()  # Make the dialog modal
        self.wait_window()  # Wait for the dialog to be closed
        return self.result

class Tab(tk.Frame):
    def __init__(self, parent, app, tab_id=None, is_default=False):
        super().__init__(parent)
        self.app = app
        self.tab_id = tab_id
        self.is_default = is_default
        self.links = []
        self.link_urls = set()
        self.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0, bg="#F0F8FF")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.vsb.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.canvas.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.links_frame = tk.Frame(self.canvas, bg="#F0F8FF")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.links_frame, anchor="nw")

        self.links_frame.bind("<Configure>", self.update_scrollregion)

    def update_scrollregion(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def add_link(self, title, url):
        try:
            if url not in self.link_urls:
                link_frame = tk.Frame(self.links_frame, bg="#f0f8ff")
                link_frame.pack(fill="x", padx=10, pady=(10,0), expand=True)

                copy_button = tk.Button(link_frame, text="Copy", command=lambda: pyperclip.copy(url), bg="#155387", fg="white", font=("Arial", 9, "bold"), relief="raised", bd=1, width=4)
                copy_button.pack(side="left", padx=5)

                serial_number = len(self.links) + 1
                if title:
                    serial_title_label = tk.Label(link_frame, text=f"{serial_number}. {title}", bg="#F0F8FF", fg="black", font=("Arial", 9), anchor="w", width=30)
                else:
                    serial_title_label = tk.Label(link_frame, text=f"{serial_number}.", bg="#F0F8FF", fg="black", font=("Arial", 9), anchor="w", width=30)
                serial_title_label.pack(side="left", padx=0)

                link_label = tk.Label(link_frame, text=url[:30] + "...", bg="#F0F8FF", fg="blue", font=("Arial", 9), cursor="hand2", anchor="w", width=26)
                link_label.pack(side="left", padx=(10, 5))
                link_label.bind("<Button-1>", lambda e: webbrowser.open(url))
                link_label.bind("<Enter>", lambda e: self.show_tooltip(link_label, url))
                link_label.bind("<Leave>", lambda e: self.hide_tooltip())

                open_button = tk.Button(link_frame, text="Open", command=lambda: webbrowser.open(url), bg="#348734", fg="white", font=("Arial", 9, "bold"), relief="raised", bd=1, width=4)
                open_button.pack(side="right", padx=(5, 0))

                delete_button = tk.Button(link_frame, text="Delete", command=lambda: self.delete_link(link_frame, url), bg="#DC1902", fg="white", font=("Arial", 9, "bold"), relief="raised", bd=1, width=5)
                delete_button.pack(side="right", padx=(0, 5))

                self.links.append(link_frame)
                self.link_urls.add(url)

                if self.tab_id is not None:
                    self.app.db_manager.cursor.execute("INSERT INTO links (tab_id, title, url) VALUES (?, ?, ?)", (self.tab_id, title, url))
                    self.app.db_manager.conn.commit()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while adding link: {e}")

    def delete_link(self, link_frame, url):
        try:
            confirm = messagebox.askyesno("Delete Link", "Are you sure you want to delete this link?")
            if confirm:
                link_frame.pack_forget()
                self.links.remove(link_frame)
                self.link_urls.remove(url)
                self.update_serial_numbers()

                if self.tab_id is not None:
                    self.app.db_manager.cursor.execute("DELETE FROM links WHERE tab_id = ? AND url = ?", (self.tab_id, url))
                    self.app.db_manager.conn.commit()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while deleting link: {e}")

    def update_serial_numbers(self):
        for i, link_frame in enumerate(self.links, start=1):
            serial_title_label = link_frame.winfo_children()[1]
            title = serial_title_label.cget("text").split(".", 1)[1].strip() if "." in serial_title_label.cget("text") else ""
            serial_title_label.config(text=f"{i}. {title}")

    def check_duplicate_link(self, url):
        return url in self.link_urls

    def show_tooltip(self, widget, text):
        self.tooltip = tk.Toplevel(self)
        self.tooltip.overrideredirect(True)
        self.tooltip.geometry("+%d+%d" % (widget.winfo_rootx() + 50, widget.winfo_rooty() + 20))
        label = tk.Label(self.tooltip, text=text, bg="black", fg="white", padx=5, pady=2)
        label.pack()

    def hide_tooltip(self):
        if hasattr(self, 'tooltip'):
            self.tooltip.destroy()

if __name__ == "__main__":
    app = LinkManager()
    app.mainloop()