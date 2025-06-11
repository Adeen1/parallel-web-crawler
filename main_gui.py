import customtkinter as ctk
from tkinter import messagebox
import re
import threading
import json
import csv
import importlib
import os

# Initialize customtkinter
ctk.set_appearance_mode("System")  # or "Dark" / "Light"
ctk.set_default_color_theme("blue")

# Mapping scraper types to modules and prompts
SCRAPER_MAP = {
    "IP Data": {
        "module": "scrape_ip_data",
        "prompt": "Enter the IP subnet (e.g., 192.168.172):",
        "validation": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){2}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    },
    "Weather Data": {
        "module": "scrape_weatherdata",
        "prompt": "Enter cities (comma-separated, e.g., pakistan/lahore, usa/new-york):",
        "validation": r"^([a-zA-Z\-]+\/[a-zA-Z\-]+)(\s*,\s*[a-zA-Z\-]+\/[a-zA-Z\-]+)*$"
    },
    "Stock Price": {
        "module": "scrape_stock_price",
        "prompt": "Enter stock symbols separated by commas (e.g., AAPL, MSFT, GOOGL):",
        "validation": r"^[A-Z]+(?:,\s*[A-Z]+)*$"
    }
}

def validate_input(scraper_type, user_input):
    """Validate user input using regex."""
    pattern = SCRAPER_MAP[scraper_type]["validation"]
    return re.fullmatch(pattern, user_input.strip()) is not None

def run_scraper(scraper_type, user_input, output_box, submit_button):
    """Run the selected scraper in a separate thread."""
    try:
        # Clear output box at the beginning
        output_box.configure(state="normal")
        output_box.delete("1.0", "end")
        output_box.configure(state="disabled")

        # Delete existing CSV if it exists
        csv_filename = "results.csv"
        if os.path.exists(csv_filename):
            os.remove(csv_filename)

        # Dynamically import the selected module
        module_name = SCRAPER_MAP[scraper_type]["module"]
        scraper_module = importlib.import_module(module_name)

        # Call its main function with user_input
        result = scraper_module.main(user_input.strip())

        # Format result
        json_result = json.dumps(result, indent=4)
        output_box.configure(state="normal")
        output_box.insert("end", json_result)
        output_box.configure(state="disabled")

        # Save as CSV
        with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if isinstance(result, list) and isinstance(result[0], dict):
                writer.writerow(result[0].keys())
                for row in result:
                    writer.writerow(row.values())
            elif isinstance(result, dict):
                writer.writerow(result.keys())
                writer.writerow(result.values())
            else:
                writer.writerow(["Result"])
                writer.writerow([str(result)])

        messagebox.showinfo("Success", f"Scraping completed! Results saved to {os.path.abspath(csv_filename)}.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{e}")
    finally:
        submit_button.configure(state="normal", text="Submit")

def submit_action(scraper_type, user_input, output_box, submit_button):
    """Validate input and start scraping."""
    if not validate_input(scraper_type, user_input):
        messagebox.showerror("Invalid Input", "Please enter valid input according to the prompt.")
        return
    
    submit_button.configure(state="disabled", text="Processing...")

    # Run scraper in a thread to keep GUI responsive
    threading.Thread(target=run_scraper, args=(scraper_type, user_input, output_box, submit_button)).start()

# GUI Setup
app = ctk.CTk()
app.title("Data Scraper Tool")
app.geometry("600x500")
app.resizable(False, False)

title_label = ctk.CTkLabel(app, text="👋 Welcome to Data Scraper!", font=ctk.CTkFont(size=20, weight="bold"))
title_label.pack(pady=20)

# Dropdown Menu
selected_scraper = ctk.StringVar(value="IP Data")
dropdown = ctk.CTkOptionMenu(app, variable=selected_scraper, values=list(SCRAPER_MAP.keys()))
dropdown.pack(pady=10)

# Input Prompt and Field
input_label = ctk.CTkLabel(app, text=SCRAPER_MAP[selected_scraper.get()]["prompt"])
input_label.pack(pady=5)

input_field = ctk.CTkEntry(app, width=400)
input_field.pack(pady=5)

# Update prompt dynamically when dropdown changes
def update_prompt(*args):
    scraper_type = selected_scraper.get()
    input_label.configure(text=SCRAPER_MAP[scraper_type]["prompt"])
    input_field.delete(0, "end")
    output_box.configure(state="normal")
    output_box.delete("1.0", "end")
    output_box.configure(state="disabled")

selected_scraper.trace_add("write", update_prompt)

# Submit Button
submit_button = ctk.CTkButton(app, text="Submit", command=lambda: submit_action(
    selected_scraper.get(), input_field.get(), output_box, submit_button))
submit_button.pack(pady=10)

# Output Box
output_label = ctk.CTkLabel(app, text="Output:")
output_label.pack(pady=5)

output_box = ctk.CTkTextbox(app, height=200, state="disabled")
output_box.pack(pady=5, padx=10, fill="both", expand=True)

app.mainloop()
