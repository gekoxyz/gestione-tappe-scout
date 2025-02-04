import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os

class ScoutManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Scout Progress Manager")
        self.data_file = "scouts_data.csv"
        
        # Initialize DataFrame
        self.scouts_df = pd.DataFrame(columns=["Name", "Age", "Year Joined"])
        if os.path.exists(self.data_file):
            self.scouts_df = pd.read_csv(self.data_file)
        
        # GUI Setup
        self.create_widgets()
        self.load_scouts()

    def create_widgets(self):
        # Input Frame
        input_frame = ttk.LabelFrame(self.root, text="Scout Details")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Name
        ttk.Label(input_frame, text="Name:").grid(row=0, column=0, sticky="w")
        self.name_entry = ttk.Entry(input_frame)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Age
        ttk.Label(input_frame, text="Age:").grid(row=1, column=0, sticky="w")
        self.age_entry = ttk.Entry(input_frame)
        self.age_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Year Joined
        ttk.Label(input_frame, text="Year Joined:").grid(row=2, column=0, sticky="w")
        self.year_entry = ttk.Entry(input_frame)
        self.year_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        ttk.Button(button_frame, text="Add Scout", command=self.add_scout).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Update Scout", command=self.update_scout).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Delete Scout", command=self.delete_scout).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Clear Fields", command=self.clear_entries).grid(row=0, column=3, padx=5)

        # List Frame
        list_frame = ttk.LabelFrame(self.root, text="Scouts List")
        list_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # Treeview
        self.tree = ttk.Treeview(list_frame, columns=("Name", "Age", "Year Joined"), show="headings")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Age", text="Age")
        self.tree.heading("Year Joined", text="Year Joined")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.pack(fill="both", expand=True)

    def load_scouts(self):
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load data from DataFrame
        for index, row in self.scouts_df.iterrows():
            self.tree.insert("", "end", values=(row["Name"], row["Age"], row["Year Joined"]))

    def add_scout(self):
        name = self.name_entry.get()
        age = self.age_entry.get()
        year = self.year_entry.get()
        
        if not all([name, age, year]):
            messagebox.showwarning("Input Error", "All fields are required!")
            return
        
        try:
            new_scout = {
                "Name": name,
                "Age": int(age),
                "Year Joined": int(year)
            }
            self.scouts_df = pd.concat([self.scouts_df, pd.DataFrame([new_scout])], ignore_index=True)
            self.scouts_df.to_csv(self.data_file, index=False)
            self.load_scouts()
            self.clear_entries()
        except ValueError:
            messagebox.showwarning("Input Error", "Age and Year must be numbers!")

    def update_scout(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a scout to update!")
            return
        
        name = self.name_entry.get()
        age = self.age_entry.get()
        year = self.year_entry.get()
        
        if not all([name, age, year]):
            messagebox.showwarning("Input Error", "All fields are required!")
            return
        
        try:
            index = self.tree.index(selected[0])
            self.scouts_df.at[index, "Name"] = name
            self.scouts_df.at[index, "Age"] = int(age)
            self.scouts_df.at[index, "Year Joined"] = int(year)
            self.scouts_df.to_csv(self.data_file, index=False)
            self.load_scouts()
            self.clear_entries()
        except ValueError:
            messagebox.showwarning("Input Error", "Age and Year must be numbers!")

    def delete_scout(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a scout to delete!")
            return
        
        index = self.tree.index(selected[0])
        self.scouts_df = self.scouts_df.drop(index).reset_index(drop=True)
        self.scouts_df.to_csv(self.data_file, index=False)
        self.load_scouts()
        self.clear_entries()

    def clear_entries(self):
        self.name_entry.delete(0, tk.END)
        self.age_entry.delete(0, tk.END)
        self.year_entry.delete(0, tk.END)

    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            self.clear_entries()
            self.name_entry.insert(0, item["values"][0])
            self.age_entry.insert(0, item["values"][1])
            self.year_entry.insert(0, item["values"][2])

if __name__ == "__main__":
    root = tk.Tk()
    app = ScoutManagerApp(root)
    root.mainloop()
