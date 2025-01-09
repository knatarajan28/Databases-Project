import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error

# Database connection details
DATABASE_HOST = "localhost"
DATABASE_USER = "root"
DATABASE_PASSWORD = "Kaunnachdi123#"
DATABASE_NAME = "business_supply"

# Connect to the database
def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host=DATABASE_HOST,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            database=DATABASE_NAME
        )
        return connection
    except Error as e:
        messagebox.showerror("Database Error", f"Error connecting to MySQL: {e}")
        return None

# Fetch procedures and their parameters
def fetch_procedures():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT SPECIFIC_NAME, PARAMETER_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.PARAMETERS
                WHERE SPECIFIC_SCHEMA = %s
                ORDER BY SPECIFIC_NAME, ORDINAL_POSITION
            """, (DATABASE_NAME,))
            procedures = {}
            for row in cursor.fetchall():
                procedure_name = row["SPECIFIC_NAME"]
                param_name = row["PARAMETER_NAME"]
                data_type = row["DATA_TYPE"]
                if procedure_name not in procedures:
                    procedures[procedure_name] = []
                procedures[procedure_name].append((param_name, data_type))
            return procedures
        except Error as e:
            messagebox.showerror("Fetch Error", f"Error fetching procedures: {e}")
        finally:
            cursor.close()
            connection.close()
    return {}

# Fetch unique views
def fetch_views():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.VIEWS
                WHERE TABLE_SCHEMA = %s
            """, (DATABASE_NAME,))
            views = sorted(set(row[0] for row in cursor.fetchall()))
            return views
        except Error as e:
            messagebox.showerror("Fetch Error", f"Error fetching views: {e}")
        finally:
            cursor.close()
            connection.close()
    return []

# Execute a stored procedure
def execute_procedure(procedure_name, params):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.callproc(procedure_name, params)
            connection.commit()
            messagebox.showinfo("Success", f"Procedure '{procedure_name}' executed successfully!")
        except Error as e:
            messagebox.showerror("Execution Error", f"Error executing procedure: {e}")
        finally:
            cursor.close()
            connection.close()

# Fetch and display view data
def fetch_view(view_name, output_area):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM {view_name}")
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            # Clear previous output
            output_area.delete(1.0, tk.END)

            # Display column headers
            output_area.insert(tk.END, f"{' | '.join(columns)}\n")
            output_area.insert(tk.END, "-" * 50 + "\n")

            # Display rows
            for row in results:
                output_area.insert(tk.END, f"{' | '.join(map(str, row))}\n")
        except Error as e:
            messagebox.showerror("Fetch Error", f"Error fetching view data: {e}")
        finally:
            cursor.close()
            connection.close()

# GUI
def create_gui():
    root = tk.Tk()
    root.title("Business Supply System - Dynamic MVP")

    procedures = fetch_procedures()
    views = fetch_views()

    # Dropdown for procedures and views
    options = list(procedures.keys()) + views
    selected_option = tk.StringVar()
    selected_option.set("Select an Option")

    ttk.Label(root, text="Select a Procedure or View:").grid(row=0, column=0, padx=10, pady=10)
    dropdown = ttk.OptionMenu(root, selected_option, *options)
    dropdown.grid(row=0, column=1, padx=10, pady=10)

    # Input fields for parameters
    input_frame = ttk.LabelFrame(root, text="Inputs")
    input_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
    input_fields = {}

    def update_inputs(*args):
        for widget in input_frame.winfo_children():
            widget.destroy()

        option = selected_option.get()
        if option in procedures:
            for i, (param_name, data_type) in enumerate(procedures[option]):
                label = ttk.Label(input_frame, text=f"{param_name} ({data_type}):")
                label.grid(row=i, column=0, padx=5, pady=5)
                entry = ttk.Entry(input_frame)
                entry.grid(row=i, column=1, padx=5, pady=5)
                input_fields[param_name] = entry

    selected_option.trace("w", update_inputs)
    #root.after(100, update_inputs) # uncomment just for add_business 
    
    # Output area for results
    output_frame = ttk.LabelFrame(root, text="Output")
    output_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
    output_area = tk.Text(output_frame, height=10, width=50)
    output_area.pack(padx=5, pady=5)

    # Execute button
    def on_execute():
        option = selected_option.get()
        if option in procedures:
            params = [entry.get() for entry in input_fields.values()]
            execute_procedure(option, params)
        elif option in views:
            fetch_view(option, output_area)
        else:
            messagebox.showwarning("Invalid Selection", "Please select a valid procedure or view.")

    execute_button = ttk.Button(root, text="Execute", command=on_execute)
    execute_button.grid(row=3, column=0, columnspan=2, pady=10)

    root.mainloop()

# Run the GUI
create_gui()
