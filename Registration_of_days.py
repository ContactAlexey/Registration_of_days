'''
Custom License Agreement

Copyright (c) 2025 Alexey

Permission is hereby granted to use this software and its source code for personal or internal use only.

🔒 Restrictions:
- You are NOT allowed to modify, copy, merge, publish, distribute, sublicense, or sell copies of this software, in whole or in part, without explicit written permission from the original creator.
- You may NOT reverse-engineer, decompile, or disassemble any part of this software.
- This software is provided "as is", without warranty of any kind.

📬 For modification rights, please contact the creator for approval.

By using this software, you agree to the terms of this license.
'''

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
import json
import datetime
import sys

def get_icon_path(file_name):
    # Determine the base path for the icon depending on whether the app is frozen (packaged) or not
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, file_name)

# --- Path to save in Documents/employee_records ---
documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
records_dir = os.path.join(documents_dir, "employee_records")
os.makedirs(records_dir, exist_ok=True)  # Create the directory if it doesn't exist
DATA_FILE = os.path.join(records_dir, "employees_data.json")

# --- Function to sort dates ---
def sort_dates(date_list):
    return sorted(date_list)

# --- Load data or initialize ---
def load_data():
    # Load existing data from JSON file or initialize with default values
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for employee in data.values():
                for type in ['vacations', 'work', 'holidays']:
                    employee[type] = sort_dates(employee[type])
            return data
    else:
        return {
            "ABYD": {"vacations": [], "work": [], "holidays": []},
            "ALEJANDRA": {"vacations": [], "work": [], "holidays": []},
            # ... (other employees)
            "RAIMOND": {"vacations": [], "work": [], "holidays": []}
        }

def save_data():
    # Save the current employee data to the JSON file
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for employee in employees.values():
            for type in ['vacations', 'work', 'holidays']:
                employee[type] = sort_dates(employee[type])
        json.dump(employees, f, indent=2, ensure_ascii=False)

employees = load_data()

def get_employee_list():
    return list(employees.keys())

# === GUI FUNCTIONS ===
def toggle_range(activate):
    # Enable or disable the end date entry based on the checkbox state
    if activate:
        end_date_entry.config(state="normal")
        end_date_entry.set_date(start_date_entry.get_date())
    else:
        end_date_entry.config(state="disabled")

def register_date(type):
    # Register a date or range of dates for an employee
    name = employee_var.get()
    start_date = start_date_entry.get_date().strftime("%Y-%m-%d")
    
    if mode_var.get():  # If range mode is selected
        end_date = end_date_entry.get_date().strftime("%Y-%m-%d")
        start_date_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        
        if start_date_dt > end_date_dt:
            messagebox.showwarning("Error", "The start date cannot be later than the end date.")
            return
        
        # Register all dates in the range
        dates_to_register = []
        duplicate_dates = []
        
        current_date = start_date_dt
        while current_date <= end_date_dt:
            date_str = current_date.strftime("%Y-%m-%d")
            if date_str in employees[name][type]:
                duplicate_dates.append(date_str)
            else:
                dates_to_register.append(date_str)
            current_date += datetime.timedelta(days=1)
        
        if duplicate_dates:
            messagebox.showwarning("Duplicate Dates", 
                                 f"The following dates were already registered:\n{', '.join(duplicate_dates)}")
        
        if dates_to_register:
            employees[name][type].extend(dates_to_register)
            employees[name][type] = sort_dates(employees[name][type])
            save_data()
            messagebox.showinfo("Success", f"{len(dates_to_register)} days of {type} have been registered for {name}.")
            update_available_dates()
    else:  # If single date mode is selected
        if start_date in employees[name][type]:
            messagebox.showwarning("Duplicate Date", f"{start_date} is already registered as {type} for {name}.")
        else:
            employees[name][type].append(start_date)
            employees[name][type] = sort_dates(employees[name][type])
            save_data()
            messagebox.showinfo("Success", f"{start_date} has been registered as a {type} day for {name}.")
            update_available_dates()

def view_dates(type):
    # Display registered dates for a specific type for the selected employee
    name = employee_var.get()
    record_text.config(state="normal")
    record_text.delete(1.0, tk.END)
    record_text.insert(tk.END, f"{type.capitalize()} of {name}:\n")
    for f in employees[name][type]:
        record_text.insert(tk.END, f" • {f}\n")
    record_text.config(state="disabled")

def update_available_dates(*args):
    # Update the dropdown of available dates to delete based on the selected employee and type
    name = employee_var.get()
    type = type_to_delete.get()
    dates = sort_dates(employees[name][type])
    date_to_delete_menu['values'] = dates
    if dates:
        date_to_delete_menu.current(0)
    else:
        date_to_delete_menu.set("")

def delete_date():
    # Delete a specific date for the selected employee and type
    name = employee_var.get()
    type = type_to_delete.get()
    date = date_to_delete_var.get()
    if date in employees[name][type]:
        employees[name][type].remove(date)
        employees[name][type] = sort_dates(employees[name][type])
        save_data()
        messagebox.showinfo("Success", f"{date} has been deleted from {type} for {name}.")
        update_available_dates()
    else:
        messagebox.showerror("Error", "Date not found.")

def export_pdf(type):
    # Export the registered dates for the selected employee and type to a PDF file
    name = employee_var.get()
    dates = sort_dates(employees[name][type])
    if not dates:
        messagebox.showwarning("No Data", f"There are no registered dates of {type} for {name}.")
        return

    base_name = f"{name}_{type}"
    num = 1
    while True:
        pdf_name = f"{base_name}_{num}.pdf"
        default_pdf_path = os.path.join(records_dir, pdf_name)
        if not os.path.exists(default_pdf_path):
            break
        num += 1

    pdf_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF Files", "*.pdf")],
        initialfile=pdf_name,
        initialdir=records_dir,
        title="Save PDF as"
    )
    
    if not pdf_path:
        return

    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 800, f"Record of {type.capitalize()} - {name}")

    c.setFont("Helvetica", 11)
    y = 770
    for f in dates:
        c.drawString(60, y, f"• {f}")
        y -= 20
        if y < 50:
            c.showPage()
            y = 800
            c.setFont("Helvetica", 11)

    c.save()
    messagebox.showinfo("PDF Saved", f"{type} PDF for {name} saved as:\n{os.path.basename(pdf_path)}")

# === GUI ===
root = tk.Tk()
root.title("Employee Records")
root.iconbitmap(get_icon_path("logo.ico"))
root.configure(bg="#e8ecf1")

root.update_idletasks()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = 900
window_height = 600
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2
root.geometry(f"{window_width}x{window_height}+{x}+{y}")
root.rowconfigure(1, weight=1)
root.columnconfigure(0, weight=1)

# Modern style
style = ttk.Style()
try:
    style.theme_use("clam")
except:
    pass

style.configure("TFrame", background="#e8ecf1")
style.configure("TLabel", font=("Arial", 10), background="#e8ecf1", foreground="#2c3e50")
style.configure("TButton", font=("Arial", 10, "bold"), background="#1f6aa5", foreground="white", padding=6)
style.map("TButton", background=[("active", "#155a8a")])
style.configure("TCombobox", padding=5)
style.configure("TLabelframe", background="#ffffff", relief="groove", padding=10)
style.configure("TLabelframe.Label", font=("Arial", 11, "bold"), background="#ffffff", foreground="#1f6aa5")

# === CONTENT ===
top_frame = ttk.Frame(root)
top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
top_frame.columnconfigure((0,1,2,3), weight=1)

data_frame = ttk.Labelframe(top_frame, text="Employee Data")
data_frame.grid(row=0, column=0, sticky="nsew", padx=5)

ttk.Label(data_frame, text="Employee:").pack(anchor="w")
employee_var = tk.StringVar()
employee_dropdown = ttk.Combobox(data_frame, textvariable=employee_var, state="readonly")
employee_dropdown['values'] = get_employee_list()
employee_dropdown.current(0)
employee_dropdown.pack(fill="x", pady=2)

ttk.Label(data_frame, text="Date:").pack(anchor="w")
start_date_entry = DateEntry(data_frame, date_pattern='yyyy-mm-dd', locale='en_US', date=datetime.date.today())
start_date_entry.pack(fill="x", pady=2)

# Checkbutton to select registration mode
mode_var = tk.BooleanVar(value=False)
ttk.Checkbutton(data_frame, text="Register date range", variable=mode_var, 
                command=lambda: toggle_range(mode_var.get())).pack(anchor="w")

# Second DateEntry for the end date of the range
ttk.Label(data_frame, text="End date:").pack(anchor="w")
end_date_entry = DateEntry(data_frame, date_pattern='yyyy-mm-dd', locale='en_US', date=datetime.date.today())
end_date_entry.pack(fill="x", pady=2)
end_date_entry.config(state="disabled")

action_frame = ttk.Labelframe(top_frame, text="Register")
action_frame.grid(row=0, column=1, sticky="nsew", padx=5)

ttk.Button(action_frame, text="Register Vacations", command=lambda: register_date("vacations")).pack(fill="x", pady=2)
ttk.Button(action_frame, text="Register Work", command=lambda: register_date("work")).pack(fill="x", pady=2)
ttk.Button(action_frame, text="Register Holiday", command=lambda: register_date("holidays")).pack(fill="x", pady=2)

view_frame = ttk.Labelframe(top_frame, text="View Records")
view_frame.grid(row=0, column=2, sticky="nsew", padx=5)

ttk.Button(view_frame, text="View Vacations", command=lambda: view_dates("vacations")).pack(fill="x", pady=2)
ttk.Button(view_frame, text="View Work", command=lambda: view_dates("work")).pack(fill="x", pady=2)
ttk.Button(view_frame, text="View Holidays", command=lambda: view_dates("holidays")).pack(fill="x", pady=2)

ttk.Button(view_frame, text="Export Vacations", command=lambda: export_pdf("vacations")).pack(fill="x", pady=2)
ttk.Button(view_frame, text="Export Work", command=lambda: export_pdf("work")).pack(fill="x", pady=2)
ttk.Button(view_frame, text="Export Holidays", command=lambda: export_pdf("holidays")).pack(fill="x", pady=2)

delete_frame = ttk.Labelframe(top_frame, text="Delete Registered Date")
delete_frame.grid(row=0, column=3, sticky="nsew", padx=5)

ttk.Label(delete_frame, text="Type of date:").pack(anchor="w")
type_to_delete = tk.StringVar(value="vacations")
type_menu = ttk.Combobox(delete_frame, textvariable=type_to_delete, values=["vacations", "work", "holidays"], state="readonly")
type_menu.pack(fill="x", pady=2)

ttk.Label(delete_frame, text="Date to delete:").pack(anchor="w")
date_to_delete_var = tk.StringVar()
date_to_delete_menu = ttk.Combobox(delete_frame, textvariable=date_to_delete_var, state="readonly")
date_to_delete_menu.pack(fill="x", pady=2)

ttk.Button(delete_frame, text="Delete Date", command=delete_date).pack(fill="x", pady=5)

# Bottom register
bottom_frame = ttk.Frame(root)
bottom_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))
bottom_frame.columnconfigure(0, weight=1)
bottom_frame.rowconfigure(0, weight=1)

record_text = tk.Text(bottom_frame, font=("Arial", 10))
record_text.grid(row=0, column=0, sticky="nsew")
scrollbar = ttk.Scrollbar(bottom_frame, orient="vertical", command=record_text.yview)
scrollbar.grid(row=0, column=1, sticky="ns")
record_text.config(yscrollcommand=scrollbar.set, state="disabled")

# Employee management
management_frame = ttk.Labelframe(root, text="Employee Management")
management_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
management_frame.columnconfigure(1, weight=1)

new_employee_var = tk.StringVar()
ttk.Label(management_frame, text="New Employee:").grid(row=0, column=0, sticky="w", padx=5)
entry_new_employee = ttk.Entry(management_frame, textvariable=new_employee_var)
entry_new_employee.grid(row=0, column=1, sticky="ew", padx=5)

def update_employee_dropdown():
    # Update the employee dropdown with sorted employee names
    sorted_employees = sorted(get_employee_list())
    employee_dropdown['values'] = sorted_employees
    if sorted_employees:
        employee_var.set(sorted_employees[0])
    else:
        employee_var.set("")

def add_employee():
    # Add a new employee to the records
    name = new_employee_var.get().strip().upper()
    if not name:
        messagebox.showwarning("Empty Input", "The name cannot be empty.")
        return
    if name in employees:
        messagebox.showwarning("Duplicate", f"The employee '{name}' already exists.")
        return
    employees[name] = {"vacations": [], "work": [], "holidays": []}
    save_data()
    update_employee_dropdown()
    messagebox.showinfo("Success", f"Employee '{name}' added.")
    new_employee_var.set("")

def delete_employee():
    # Delete the selected employee from the records
    name = employee_var.get()
    if not name:
        messagebox.showwarning("No Employee Selected", "You must select an employee.")
        return
    if messagebox.askyesno("Confirm", f"Are you sure you want to delete '{name}'?"):
        del employees[name]
        save_data()
        update_employee_dropdown()
        messagebox.showinfo("Deleted", f"Employee '{name}' deleted.")

ttk.Button(management_frame, text="Add Employee", command=add_employee).grid(row=0, column=2, padx=5)
ttk.Button(management_frame, text="Delete Selected Employee", command=delete_employee).grid(row=0, column=3, padx=5)

employee_var.trace_add("write", update_available_dates)
type_to_delete.trace_add("write", update_available_dates)
update_available_dates()
update_employee_dropdown()
root.protocol("WM_DELETE_WINDOW", lambda: (save_data(), root.destroy()))
root.mainloop()
