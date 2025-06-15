
import customtkinter as ctk
import tkinter as tk
import re
import time
import threading
import importlib
import json
import os
import csv

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

SCRAPER_MAP = {
    "IP Data": {
        "module": "scrape_ip_data",
        "prompt": "Enter the IP subnet:",
        "example": "e.g., 192.168.172",
        "validation": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){2}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
        "csv_filename": "results_ip_data.csv"
    },
    "Weather Data": {
        "module": "scrape_weatherdata",
        "prompt": "Enter cities (comma-separated):",
        "example": "e.g., pakistan/lahore, usa/new-york",
        "validation": r"^([a-zA-Z\-]+\/[a-zA-Z\-]+)(\s*,\s*[a-zA-Z\-]+\/[a-zA-Z\-]+)*$",
        "csv_filename": "results_weather_data.csv"
    },
    "Stock Price": {
        "module": "scrape_stock_price",
        "prompt": "Enter stock symbols (comma-separated):",
        "example": "e.g., AAPL, MSFT, GOOGL",
        "validation": r"^[A-Z]+(?:,\s*[A-Z]+)*$",
        "csv_filename": "results_stock_price.csv"
    },
    "ASN Data": {
        "module": "scrape_asn_data",
        "prompt": "Enter ASN Numbers range",
        "example": "e.g., 1570-1579",
        "validation": r"^[0-9]+-[0-9]+$",
        "csv_filename": "results_asn_data.csv"
    }
    
}

def validate_input(scraper_type, user_input):
    """Validates user input against a predefined regex pattern."""
    pattern = SCRAPER_MAP[scraper_type]["validation"]
    return re.fullmatch(pattern, user_input.strip()) is not None

def highlight_json(output_widget, json_str):
    """Highlights JSON syntax in the output text widget."""
    output_widget.configure(state="normal")
    output_widget.delete("1.0", "end")
    i = 0
    while i < len(json_str):
        if json_str[i] == '"':
            start = i
            i += 1
            while i < len(json_str) and json_str[i] != '"':
                if json_str[i] == '\\': i += 1  # Skip escaped chars
                i += 1
            i += 1
            word = json_str[start:i]
            if json_str[i:i+1] == ':':
                output_widget.insert("end", word, "key")
            else:
                output_widget.insert("end", word, "value")
        elif json_str[i].isdigit() or json_str[i] == '-':
            start = i
            while i < len(json_str) and (json_str[i].isdigit() or json_str[i] in ".eE-+"):
                i += 1
            output_widget.insert("end", json_str[start:i], "number")
        elif json_str[i:i+4] == "true" or json_str[i:i+5] == "false":
            bool_val = "true" if json_str[i:i+4] == "true" else "false"
            output_widget.insert("end", bool_val, "boolean")
            i += len(bool_val)
        else:
            output_widget.insert("end", json_str[i])
            i += 1
    output_widget.configure(state="disabled")

def run_scraper(scraper_type, user_input, output_box, button, exec_label, message_label, app):
    """
    Executes the selected scraper module, processes the result,
    saves it to a CSV, and updates the GUI.
    """
    start_time = time.time()    
    try:
        # Clear previous outputs and messages
        output_box.configure(state="normal")
        output_box.delete("1.0", "end")
        output_box.configure(state="disabled")
        exec_label.configure(text="")
        message_label.configure(text="", text_color="white") # Clear previous message

        # Dynamically import the scraper module and run its main function
        module = importlib.import_module(SCRAPER_MAP[scraper_type]["module"])
        result = module.main(user_input.strip())
        json_str = json.dumps(result, indent=4)

        # Handle CSV file appending
        csv_filename = SCRAPER_MAP[scraper_type]["csv_filename"]
        file_exists = os.path.exists(csv_filename)

        with open(csv_filename, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Write headers only if the file is new and the result is structured
            if isinstance(result, list) and result and isinstance(result[0], dict):
                if not file_exists:
                    writer.writerow(result[0].keys())
                for row in result:
                    writer.writerow(row.values())
            elif isinstance(result, dict):
                if not file_exists:
                    writer.writerow(result.keys())
                writer.writerow(result.values())
            else: # For single, non-structured results
                if not file_exists:
                    writer.writerow(["Result"])
                writer.writerow([str(result)])

        # Update GUI with results
        highlight_json(output_box, json_str)
        duration = round(time.time() - start_time, 2)
        exec_label.configure(text=f"✔ Completed in {duration} seconds", text_color="lightgreen")
        message_label.configure(text="Scraping completed successfully!", text_color="green")
    except Exception as e:
        message_label.configure(text=f"Error: {str(e)}", text_color="red")
    finally:
        button.configure(state="normal", text="Submit")

def submit(scraper_type, user_input, entry, output_box, button, exec_label, message_label, app):
    """Handles the submit action, including input validation and starting the scraper thread."""
    message_label.configure(text="", text_color="white") # Clear previous message
    if not validate_input(scraper_type, user_input.get()):
        entry.configure(border_color="red")
        message_label.configure(text="Invalid input! Please check the format.", text_color="orange")
        return
    entry.configure(border_color="green")
    button.configure(state="disabled", text="Processing...")
    threading.Thread(target=run_scraper, args=(scraper_type, user_input.get(), output_box, button, exec_label, message_label, app)).start()

# GUI Setup
app = ctk.CTk()
app.title("Parallel Data Scraper")
app.geometry("800x700") # Set an initial size
app.resizable(False, False) # Disable resizing if you want fixed size

# Make the window movable
def start_move(event):
    """Records the initial mouse position for window dragging."""
    app.x = event.x
    app.y = event.y

def do_move(event):
    """Moves the window based on mouse drag."""
    deltax = event.x - app.x
    deltay = event.y - app.y
    x = app.winfo_x() + deltax
    y = app.winfo_y() + deltay
    app.geometry(f"+{x}+{y}")

app.bind("<ButtonPress-1>", start_move)
app.bind("<B1-Motion>", do_move)

frame = ctk.CTkFrame(app)
frame.pack(pady=20, padx=40, fill="both", expand=True)

title = ctk.CTkLabel(frame, text="👋 Welcome to Parallel Data Scraper!", font=("Segoe UI", 24, "bold"))
title.pack(pady=20)

scraper_type = tk.StringVar(value="IP Data")
dropdown = ctk.CTkOptionMenu(frame, values=list(SCRAPER_MAP.keys()), variable=scraper_type)
dropdown.pack(pady=10)

# Message label for success/error
message_label = ctk.CTkLabel(frame, text="", font=("Segoe UI", 13), text_color="white")
message_label.pack(pady=(5, 0))

prompt_label = ctk.CTkLabel(frame, text=SCRAPER_MAP[scraper_type.get()]["prompt"], font=("Segoe UI", 14))
prompt_label.pack(pady=(10, 0))

example_label = ctk.CTkLabel(frame, text=SCRAPER_MAP[scraper_type.get()]["example"], font=("Segoe UI", 12), text_color="gray")
example_label.pack(pady=(0, 5))


input_var = tk.StringVar()
input_entry = ctk.CTkEntry(frame, textvariable=input_var, width=400)
input_entry.pack()

submit_btn = ctk.CTkButton(frame, text="Submit", command=lambda: submit(
    scraper_type.get(), input_var, input_entry, output_box, submit_btn, exec_label, message_label, app))
submit_btn.pack(pady=10)

output_box = tk.Text(frame, height=20, bg="#1e1e1e", fg="white", insertbackground="white", wrap="none")
output_box.tag_config("key", foreground="#7FD7FF")
output_box.tag_config("value", foreground="#B2FF59")
output_box.tag_config("number", foreground="#FFA500")
output_box.tag_config("boolean", foreground="#BA68C8")
output_box.pack(pady=10, fill="both", expand=True)

exec_label = ctk.CTkLabel(frame, text="", font=("Segoe UI", 12))
exec_label.pack()

copy_btn = ctk.CTkButton(frame, text="📋 Copy JSON", command=lambda: app.clipboard_append(output_box.get("1.0", "end")))
copy_btn.pack(pady=5)

def update_prompt(*_):
    """Updates the prompt and example labels when the scraper type changes."""
    selected_scraper = scraper_type.get()
    prompt_label.configure(text=SCRAPER_MAP[selected_scraper]["prompt"])
    example_label.configure(text=SCRAPER_MAP[selected_scraper]["example"])
    
    input_var.set("") # Clear input field
    output_box.configure(state="normal")
    output_box.delete("1.0", "end")
    output_box.configure(state="disabled")
    exec_label.configure(text="")
    message_label.configure(text="", text_color="white") # Clear messages on type change

scraper_type.trace("w", update_prompt)

app.bind("<Escape>", lambda e: app.destroy())
app.mainloop()
