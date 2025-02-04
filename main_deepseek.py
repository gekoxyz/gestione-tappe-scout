import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os

# Define the CSV file and expected columns.
CSV_FILE = "scouts.csv"
COLUMNS = ["Name", "Age", "Year Joined"]

def load_data():
    """Load data from the CSV file into a pandas DataFrame.
    If the file does not exist, create it with the appropriate columns."""
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
        except pd.errors.EmptyDataError:
            # File exists but is empty; create a new DataFrame.
            df = pd.DataFrame(columns=COLUMNS)
    else:
        df = pd.DataFrame(columns=COLUMNS)
        df.to_csv(CSV_FILE, index=False)
    return df

def save_data(df):
    """Save the DataFrame to the CSV file."""
    df.to_csv(CSV_FILE, index=False)

def refresh_treeview():
    """Clear and repopulate the Treeview with data from the DataFrame."""
    for item in tree.get_children():
        tree.delete(item)
    for idx, row in df.iterrows():
        # Use idx as the unique id for each treeview item.
        tree.insert("", "end", iid=idx, values=(row["Name"], row["Age"], row["Year Joined"]))

def add_record():
    """Open a window to add a new scout record."""
    add_win = tk.Toplevel(root)
    add_win.title("Add Scout")

    # Labels and entry fields
    tk.Label(add_win, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    name_entry = tk.Entry(add_win)
    name_entry.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(add_win, text="Age:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    age_entry = tk.Entry(add_win)
    age_entry.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(add_win, text="Year Joined:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    year_entry = tk.Entry(add_win)
    year_entry.grid(row=2, column=1, padx=5, pady=5)

    def submit_add():
        name = name_entry.get().strip()
        age = age_entry.get().strip()
        year_joined = year_entry.get().strip()
        if not name or not age or not year_joined:
            messagebox.showerror("Input Error", "All fields must be filled!")
            return

        # Append the new record to the DataFrame.
        global df
        new_row = {"Name": name, "Age": age, "Year Joined": year_joined}
        # Option 1: Using df.loc to add a new row.
        df.loc[len(df)] = new_row
        save_data(df)
        refresh_treeview()
        add_win.destroy()

    tk.Button(add_win, text="Add", command=submit_add).grid(row=3, column=0, columnspan=2, pady=10)

def edit_record():
    """Open a window to edit the selected scout record."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Selection Error", "Please select a record to edit.")
        return

    idx = selected[0]
    row_data = df.loc[int(idx)]
    edit_win = tk.Toplevel(root)
    edit_win.title("Edit Scout")

    tk.Label(edit_win, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    name_entry = tk.Entry(edit_win)
    name_entry.grid(row=0, column=1, padx=5, pady=5)
    name_entry.insert(0, row_data["Name"])

    tk.Label(edit_win, text="Age:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    age_entry = tk.Entry(edit_win)
    age_entry.grid(row=1, column=1, padx=5, pady=5)
    age_entry.insert(0, row_data["Age"])

    tk.Label(edit_win, text="Year Joined:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    year_entry = tk.Entry(edit_win)
    year_entry.grid(row=2, column=1, padx=5, pady=5)
    year_entry.insert(0, row_data["Year Joined"])

    def submit_edit():
        name = name_entry.get().strip()
        age = age_entry.get().strip()
        year_joined = year_entry.get().strip()
        if not name or not age or not year_joined:
            messagebox.showerror("Input Error", "All fields must be filled!")
            return

        global df
        df.loc[int(idx), "Name"] = name
        df.loc[int(idx), "Age"] = age
        df.loc[int(idx), "Year Joined"] = year_joined
        save_data(df)
        refresh_treeview()
        edit_win.destroy()

    tk.Button(edit_win, text="Update", command=submit_edit).grid(row=3, column=0, columnspan=2, pady=10)

def delete_record():
    """Delete the selected scout record after confirmation."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Selection Error", "Please select a record to delete.")
        return

    confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected record?")
    if confirm:
        idx = selected[0]
        global df
        # Drop the record and reset the index so that our iid mapping remains consistent.
        df = df.drop(int(idx)).reset_index(drop=True)
        save_data(df)
        refresh_treeview()

# --- Main Application GUI ---

root = tk.Tk()
root.title("Scout Progress Manager")
root.geometry("400x300")

# Create the Treeview to display scout records.
tree = ttk.Treeview(root, columns=COLUMNS, show="headings")
for col in COLUMNS:
    tree.heading(col, text=col)
    tree.column(col, width=120, anchor="center")
tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Create a frame to hold the CRUD buttons.
button_frame = tk.Frame(root)
button_frame.pack(pady=5)

tk.Button(button_frame, text="Add Scout", command=add_record).pack(side=tk.LEFT, padx=5)
tk.Button(button_frame, text="Edit Scout", command=edit_record).pack(side=tk.LEFT, padx=5)
tk.Button(button_frame, text="Delete Scout", command=delete_record).pack(side=tk.LEFT, padx=5)

# Load initial data from the CSV file and display it.
df = load_data()
refresh_treeview()

root.mainloop()

