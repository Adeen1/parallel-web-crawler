import customtkinter as ctk
import tkinter as tk
import re
import time
import threading
import importlib
import json
import os
import csv
from PIL import Image # Required for CTkImage

# --- Configuration ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue") # We'll override specific colors manually

# Define custom colors
HEADER_COLOR = "#FF8400"  # Dark Red / Maroon
BUTTON_COLOR = "#2A65A5"  # Brown / Muted Red
BUTTON_HOVER_COLOR = "#FF8800" # IndianRed for hover
TEXT_COLOR = "white"
SUB_TEXT_COLOR = "#E0E0E0" # Lighter white for descriptions
CARD_BG_COLOR = "#333333" # Slightly lighter dark for cards
DEFAULT_BORDER_COLOR = "#555555" # Darker gray for borders
ACCENT_COLOR = "#F6FF00" # Light blue for specific labels (e.g., card names)

# --- App Setup ---
app = ctk.CTk()
app.title("Parallel Data Scraper")
app.state('zoomed')
app.geometry("1200x800")

# Make window movable (Optional, usually not needed with 'zoomed')
def start_move(event):
    app.x = event.x
    app.y = event.y

def do_move(event):
    deltax = event.x - app.x
    deltay = event.y - app.y
    x = app.winfo_x() + deltax
    y = app.winfo_y() + deltay
    app.geometry(f"+{x}+{y}")

app.bind("<ButtonPress-1>", start_move)
app.bind("<B1-Motion>", do_move)

# --- Scraper Map (unchanged) ---
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

# --- Utility Functions ---
def validate_input(scraper_type, user_input):
    pattern = SCRAPER_MAP[scraper_type]["validation"]
    return re.fullmatch(pattern, user_input.strip()) is not None

def highlight_json(output_widget, json_str):
    output_widget.configure(state="normal")
    output_widget.delete("1.0", "end")
    i = 0
    while i < len(json_str):
        if json_str[i] == '"':
            start = i
            i += 1
            while i < len(json_str) and json_str[i] != '"':
                if json_str[i] == '\\': i += 1
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
        elif json_str[i:i+4].lower() == "true" or json_str[i:i+5].lower() == "false":
            bool_val = "true" if json_str[i:i+4].lower() == "true" else "false"
            output_widget.insert("end", bool_val, "boolean")
            i += len(bool_val)
        elif json_str[i:i+4].lower() == "null":
            output_widget.insert("end", "null", "null")
            i += 4
        else:
            output_widget.insert("end", json_str[i])
            i += 1
    output_widget.configure(state="disabled")

def run_scraper(scraper_type, user_input, output_box, button, exec_label, message_label):
    start_time = time.time()
    try:
        output_box.configure(state="normal")
        output_box.delete("1.0", "end")
        output_box.configure(state="disabled")
        exec_label.configure(text="")
        message_label.configure(text="", text_color=TEXT_COLOR)

        try:
            module = importlib.import_module(SCRAPER_MAP[scraper_type]["module"])
        except ModuleNotFoundError:
            message_label.configure(text=f"Error: Scraper module '{SCRAPER_MAP[scraper_type]['module']}.py' not found. Please ensure the scraper files are in the same directory.", text_color="red")
            return

        result = module.main(user_input.strip())
        json_str = json.dumps(result, indent=4)

        csv_filename = SCRAPER_MAP[scraper_type]["csv_filename"]
        file_exists = os.path.exists(csv_filename)

        with open(csv_filename, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if isinstance(result, list) and result and isinstance(result[0], dict):
                if not file_exists:
                    writer.writerow(result[0].keys())
                for row in result:
                    writer.writerow(row.values())
            elif isinstance(result, dict):
                if not file_exists:
                    writer.writerow(result.keys())
                writer.writerow(result.values())
            else:
                if not file_exists:
                    writer.writerow(["Result"])
                writer.writerow([str(result)])

        highlight_json(output_box, json_str)
        duration = round(time.time() - start_time, 2)
        exec_label.configure(text=f"✔ Completed in {duration} seconds", text_color="lightgreen")
        message_label.configure(text="Scraping completed successfully!", text_color="green")
    except Exception as e:
        message_label.configure(text=f"Error: {str(e)}", text_color="red")
    finally:
        button.configure(state="normal", text="Submit")

def submit(scraper_type, user_input, entry, output_box, button, exec_label, message_label):
    message_label.configure(text="", text_color=TEXT_COLOR)
    if not validate_input(scraper_type, user_input.get()):
        entry.configure(border_color="red")
        message_label.configure(text="Invalid input! Please check the format.", text_color="orange")
        return
    entry.configure(border_color="green")
    button.configure(state="disabled", text="Processing...")
    threading.Thread(target=run_scraper, args=(scraper_type, user_input.get(), output_box, button, exec_label, message_label)).start()

# Hover functions for cards
def on_enter(event, card):
    card.configure(border_color=BUTTON_HOVER_COLOR) # Highlight color on hover

def on_leave(event, card, original_border_color=DEFAULT_BORDER_COLOR):
    card.configure(border_color=original_border_color) # Revert to original color

# --- Navigation Bar ---
navbar_frame = ctk.CTkFrame(app, height=50, corner_radius=0, fg_color="#222222") # Darker navbar
navbar_frame.pack(side="top", fill="x")
navbar_frame.pack_propagate(False)

button_frame = ctk.CTkFrame(navbar_frame, fg_color="transparent")
button_frame.pack(expand=True)

# --- Scrollable Main Content Frame ---
scroll_frame = ctk.CTkScrollableFrame(app, corner_radius=10, fg_color="#1a1a1a", scrollbar_button_color=BUTTON_COLOR, scrollbar_button_hover_color=BUTTON_HOVER_COLOR) # Darker background
scroll_frame.pack(pady=10, padx=20, fill="both", expand=True) # Reduced padx

# --- Header Block (Logo + Title/Description) ---
header_block = ctk.CTkFrame(scroll_frame, fg_color="transparent", corner_radius=0)
header_block.pack(pady=(10, 30), padx=20, fill="x")

# Configure grid for header block
header_block.columnconfigure(0, weight=4) # 40% for logo
header_block.columnconfigure(1, weight=6) # 60% for text content
header_block.rowconfigure(0, weight=1) # Only one row needed, text will be in second virtual row in this column

# Load the logo (initially as a placeholder, then resized)
global_spider_logo = None # Declare as global to be accessible in resize_logo
logo_label = None # Declare as global to be accessible in resize_logo

try:
    original_image = Image.open("spider_logo.png") # Changed filename to match uploaded
    # Store the original image to maintain quality during resizing
    global_spider_logo = ctk.CTkImage(light_image=original_image,
                                      dark_image=original_image,
                                      size=(1,1)) # Initial dummy size, will be updated
    logo_label = ctk.CTkLabel(header_block, image=global_spider_logo, text="")
    # Corrected 'rowspan' from 'rowspanc'
    logo_label.grid(row=0, column=0, padx=(0, 20), pady=(10,10), sticky="nsew", rowspan=2)
except FileNotFoundError:
    print("Warning: image_b9131f.png not found. Please place it in the root directory or update the path.")
    # Fallback if image is not found, ensuring layout doesn't break
    logo_label = ctk.CTkLabel(header_block, text="[Image Not Found]", font=("Segoe UI", 16), text_color="red")
    logo_label.grid(row=0, column=0, padx=(0, 20), pady=(10,10), sticky="nsew", rowspan=2)

def resize_logo(event=None):
    if global_spider_logo and logo_label and header_block.winfo_width() > 0:
        header_width = header_block.winfo_width()
        target_logo_width = int(header_width * 0.4) # 40% of header width

        # Get original image dimensions from the stored CTkImage
        original_width, original_height = global_spider_logo._light_image.size

        if original_width > 0 and original_height > 0:
            aspect_ratio = original_height / original_width
            target_logo_height = int(target_logo_width * aspect_ratio)

            # Ensure the logo doesn't overflow vertically if the header block's row is constrained
            # This is a heuristic to prevent extreme stretching if the available height is small
            if target_logo_height > header_block.winfo_height() * 0.9 and header_block.winfo_height() > 0:
                target_logo_height = int(header_block.winfo_height() * 0.9)
                target_logo_width = int(target_logo_height / aspect_ratio)


            # Only update if size is reasonable and different to avoid infinite loops
            current_image_size = global_spider_logo.cget("size")
            if current_image_size != (target_logo_width, target_logo_height) and target_logo_width > 0 and target_logo_height > 0:
                global_spider_logo.configure(size=(target_logo_width, target_logo_height))
                logo_label.configure(image=global_spider_logo) # Update logo_label image to force redraw
                # print(f"Resized logo to: {target_logo_width}x{target_logo_height}") # For debugging

# Bind the resize function to the header_block's Configure event
header_block.bind("<Configure>", resize_logo)

text_content_frame = ctk.CTkFrame(header_block, fg_color="transparent")
text_content_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 0), pady=(0,0), rowspan=2) # Spanning 2 virtual rows for title/description

# We need to ensure the grid rows are configured in text_content_frame as well for alignment
text_content_frame.rowconfigure(0, weight=1) # For title
text_content_frame.rowconfigure(1, weight=1) # For description

header_title = ctk.CTkLabel(text_content_frame, text="Parallel Web Scraper", font=("Segoe UI", 48, "bold"), text_color=HEADER_COLOR, anchor="w")
header_title.grid(row=0, column=0, pady=(0, 5), sticky="w") # Use grid here, align to west

description_text = (
    "This application efficiently extracts diverse data from the web using parallel processing.\n"
    "Choose a scraper type, provide your input, and get structured data in real-time."
)
header_description = ctk.CTkLabel(text_content_frame, text=description_text, font=("Segoe UI", 16), text_color=SUB_TEXT_COLOR, wraplength=700, justify="left", anchor="w")
header_description.grid(row=1, column=0, sticky="w") # Use grid here, align to west


# --- Scraper Section ---
# This label serves as a target for navigation
scraper_section_anchor = ctk.CTkLabel(scroll_frame, text="", fg_color="transparent")
scraper_section_anchor.pack() # Keep it small, just for positioning

title = ctk.CTkLabel(scroll_frame, text="⚡ Scraper Interface", font=("Segoe UI", 32, "bold"), text_color=HEADER_COLOR)
title.pack(pady=(20, 20))

scraper_type = tk.StringVar(value="IP Data")
dropdown = ctk.CTkOptionMenu(scroll_frame, values=list(SCRAPER_MAP.keys()), variable=scraper_type,
                             font=("Segoe UI", 14), dropdown_font=("Segoe UI", 14),
                             button_color=BUTTON_COLOR, button_hover_color=BUTTON_HOVER_COLOR, text_color=TEXT_COLOR)
dropdown.pack(pady=10)

message_label = ctk.CTkLabel(scroll_frame, text="", font=("Segoe UI", 13), text_color=TEXT_COLOR)
message_label.pack(pady=5)

prompt_label = ctk.CTkLabel(scroll_frame, text=SCRAPER_MAP[scraper_type.get()]["prompt"], font=("Segoe UI", 16, "bold"), text_color=TEXT_COLOR)
prompt_label.pack(pady=(10, 0))

example_label = ctk.CTkLabel(scroll_frame, text=SCRAPER_MAP[scraper_type.get()]["example"], font=("Segoe UI", 12), text_color=DEFAULT_BORDER_COLOR)
example_label.pack(pady=(0, 10))

input_var = tk.StringVar()
input_entry = ctk.CTkEntry(scroll_frame, textvariable=input_var, width=500, font=("Segoe UI", 14),
                           border_color=DEFAULT_BORDER_COLOR, fg_color="#1e1e1e", text_color=TEXT_COLOR)
input_entry.pack(pady=10)

submit_btn = ctk.CTkButton(scroll_frame, text="Submit", command=lambda: submit(scraper_type.get(), input_var, input_entry, output_box, submit_btn, exec_label, message_label),
                           font=("Segoe UI", 16, "bold"), height=40, fg_color=BUTTON_COLOR, hover_color=BUTTON_HOVER_COLOR, text_color=TEXT_COLOR)
submit_btn.pack(pady=15)

output_box = tk.Text(scroll_frame, height=15, bg="#1e1e1e", fg=TEXT_COLOR, insertbackground=TEXT_COLOR, wrap="none",
                     font=("Consolas", 12))
output_box.tag_config("key", foreground="#7FD7FF")
output_box.tag_config("value", foreground="#B2FF59")
output_box.tag_config("number", foreground="#FFA500")
output_box.tag_config("boolean", foreground="#BA68C8")
output_box.tag_config("null", foreground="#808080")
output_box.pack(pady=10, fill="x", padx=40)

exec_label = ctk.CTkLabel(scroll_frame, text="", font=("Segoe UI", 12), text_color=TEXT_COLOR)
exec_label.pack(pady=5)

copy_btn = ctk.CTkButton(scroll_frame, text="📋 Copy JSON", command=lambda: app.clipboard_append(output_box.get("1.0", "end")),
                         font=("Segoe UI", 14), fg_color=BUTTON_COLOR, hover_color=BUTTON_HOVER_COLOR, text_color=TEXT_COLOR)
copy_btn.pack(pady=5)

# --- Team Section ---
team_title = ctk.CTkLabel(scroll_frame, text="👩‍💻 Project Team Members", font=("Segoe UI", 28, "bold"), text_color=HEADER_COLOR)
team_title.pack(pady=(40, 15))

team_data = [
    ("Noor Fatima", "Scraped weather-related data like temperature, forecast and location updates."),
    ("Maryam Bakhtyar", "Scraped live stock prices, company names and financial summaries."),
    ("Adeen Zia", "Scraped geolocation, ISP details and IP metadata from IP tracking websites."),
    ("Adeel Ahmad", "Scraped ASN data from ipinfo. ASN is an identifier for network routing.")
]

# Create a container for team cards to arrange them in a grid
team_cards_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
team_cards_container.pack(pady=10, padx=20, fill="x", expand=True)

# Configure grid for two columns
team_cards_container.columnconfigure(0, weight=1)
team_cards_container.columnconfigure(1, weight=1)

for i, (name, detail) in enumerate(team_data):
    card = ctk.CTkFrame(team_cards_container, corner_radius=12, border_width=1, border_color=DEFAULT_BORDER_COLOR, fg_color=CARD_BG_COLOR)
    row = i // 2
    col = i % 2
    card.grid(row=row, column=col, padx=10, pady=8, sticky="nsew")

    ctk.CTkLabel(card, text=name, font=("Segoe UI", 18, "bold"), text_color=ACCENT_COLOR).pack(anchor="w", padx=15, pady=(15, 0))
    ctk.CTkLabel(card, text=detail, font=("Segoe UI", 13), wraplength=450, justify="left", text_color=SUB_TEXT_COLOR).pack(anchor="w", padx=15, pady=(0, 15))
    card.bind("<Enter>", lambda event, c=card: on_enter(event, c))
    card.bind("<Leave>", lambda event, c=card: on_leave(event, c))

# --- Scraper Info Section ---
info_title = ctk.CTkLabel(scroll_frame, text="🔍 Scraper Descriptions", font=("Segoe UI", 28, "bold"), text_color=HEADER_COLOR)
info_title.pack(pady=(40, 15))

# Updated scraper_info with sources and schemas
scraper_info = {
    "IP Data": {
        "description": "Extracts geolocation, ISP, and metadata from IP addresses.",
        "from_website": "ipinfo.io",
        "schema": {
            "ip": "1.1.1.15",
            "City": "Brisbane",
            "State": "Queensland",
            "Country": "Australia",
            "Postal": "4101",
            "Local time": "04:51 PM, Wednesday, June 18, 2025",
            "Timezone": "Australia/Brisbane",
            "Coordinates": "-27.4816,153.0175",
            "ASN": "AS13335 (/AS13335)",
            "Hostname": "No Hostname",
            "Range": "1.1.1.0/24 (/AS13335/1.1.1.0/24)",
            "Company": "APNIC and Cloudflare DNS Resolver project",
            "Hosted domains": "0",
            "Privacy": "True",
            "Anycast": "True",
            "ASN type": "Hosting",
            "Abuse contact": "helpdesk@apnic.net (mailto:helpdesk@apnic.net)"
        }
    },
    "Weather Data": {
        "description": "Collects real-time temperature and forecasts from weather APIs.",
        "from_website": "www.timeanddate.com",
        "schema": {
            "city": "pakistan/lahore",
            "temperature": "36\u00a0\u00b0C",
            "condition": "Passing clouds.",
            "visibility": "6\u00a0km",
            "pressure": "999 mbar",
            "humidity": "44%",
            "dew_point": "22\u00a0\u00b0C",
            "forecast": "N/A",
            "timestamp": "2025-06-18 11:54:33",
            "source": "https://www.timeanddate.com/weather/pakistan/lahore"
        }
    },
    "Stock Price": {
        "description": "Fetches stock prices and financial info from trading platforms.",
        "from_website": "finance.yahoo.com, www.marketwatch.com",
        "schema": {
            "symbol": "AAPL",
            "source": "https://finance.yahoo.com/quote/AAPL",
            "price": "5,992.25",
            "change": "+7.25",
            "percent_change": "-2.64%"
        }
    },
    "ASN Data": {
        "description": "Fetches Autonomous System Number details from internet registries.",
        "from_website": "ipinfo.io",
        "schema": {
            "asn": "AS1572",
            "Country": "United States (/countries/us)",
            "Website": "mail.mil (https://host.io/mail.mil)",
            "Hosted domains": "0",
            "Number of IPv4": "0",
            "Number of IPv6": "0",
            "ASN type": "Inactive",
            "Registry": "arin",
            "Allocated": "19 years ago on Apr 03, 2006",
            "Updated": "16 years ago on May 26, 2009"
        }
    }
}

# Create a container for info cards
info_cards_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
info_cards_container.pack(pady=10, padx=20, fill="x", expand=True)

# Configure grid for ONE column for info cards
info_cards_container.columnconfigure(0, weight=1) # Only one column now

for i, (key, data) in enumerate(scraper_info.items()):
    card = ctk.CTkFrame(info_cards_container, corner_radius=12, border_width=1, border_color=DEFAULT_BORDER_COLOR, fg_color=CARD_BG_COLOR)
    # Place one card per row
    card.grid(row=i, column=0, padx=10, pady=8, sticky="ew") # Removed col parameter and sticky now "ew"

    # Card Title
    ctk.CTkLabel(card, text=key, font=("Segoe UI", 17, "bold"), text_color=ACCENT_COLOR).pack(anchor="w", padx=15, pady=(15, 0))

    # General Description
    ctk.CTkLabel(card, text=data["description"], font=("Segoe UI", 13), wraplength=700, justify="left", text_color=SUB_TEXT_COLOR).pack(anchor="w", padx=15, pady=(0, 5))

    # Scraping From
    ctk.CTkLabel(card, text=f"Scraping from: {data['from_website']}", font=("Segoe UI", 13, "italic"), text_color=SUB_TEXT_COLOR).pack(anchor="w", padx=15, pady=(0, 5))

    # Schema Header
    ctk.CTkLabel(card, text="Schema:", font=("Segoe UI", 14, "bold"), text_color=TEXT_COLOR).pack(anchor="w", padx=15, pady=(5, 5))

    # Schema JSON (beautified)
    schema_text = json.dumps(data["schema"], indent=2)
    schema_textbox = ctk.CTkTextbox(card, height=150, width=800, corner_radius=8,
                                    fg_color="#1e1e1e", text_color="#B2FF59",  # Greenish color for JSON
                                    font=("Consolas", 11), wrap="word",  # Use "word" wrap for JSON readability
                                    border_color=DEFAULT_BORDER_COLOR)
    schema_textbox.insert("end", schema_text)
    schema_textbox.configure(state="disabled") # Make it read-only
    schema_textbox.pack(anchor="center", padx=15, pady=(0, 15), fill="x", expand=True)


    card.bind("<Enter>", lambda event, c=card: on_enter(event, c))
    card.bind("<Leave>", lambda event, c=card: on_leave(event, c))

# --- Navigation Scroll Functions ---
# These functions will scroll to the top of their respective sections
def scroll_to_scraper():
    # Scroll to the anchor point for the scraper section
    if scraper_section_anchor.winfo_ismapped(): # Check if widget is mapped (rendered)
        scroll_frame.after(100, lambda: scroll_frame._parent_canvas.yview_moveto(scraper_section_anchor.winfo_y() / scroll_frame._parent_canvas.winfo_height()))

def scroll_to_team():
    if team_title.winfo_ismapped():
        scroll_frame.after(100, lambda: scroll_frame._parent_canvas.yview_moveto(team_title.winfo_y() / scroll_frame._parent_canvas.winfo_height()))

def scroll_to_info():
    if info_title.winfo_ismapped():
        scroll_frame.after(100, lambda: scroll_frame._parent_canvas.yview_moveto(info_title.winfo_y() / scroll_frame._parent_canvas.winfo_height()))

# Navbar Buttons (defined after scroll functions for command)
scraper_btn = ctk.CTkButton(button_frame, text="Scraper", command=scroll_to_scraper,
                            font=("Segoe UI", 15, "bold"), fg_color="transparent", hover_color="#3a3a3a", text_color=TEXT_COLOR)
scraper_btn.pack(side="left", padx=15, pady=5)

team_btn = ctk.CTkButton(button_frame, text="Team", command=scroll_to_team,
                         font=("Segoe UI", 15, "bold"), fg_color="transparent", hover_color="#3a3a3a", text_color=TEXT_COLOR)
team_btn.pack(side="left", padx=15, pady=5)

info_btn = ctk.CTkButton(button_frame, text="Info", command=scroll_to_info,
                         font=("Segoe UI", 15, "bold"), fg_color="transparent", hover_color="#3a3a3a", text_color=TEXT_COLOR)
info_btn.pack(side="left", padx=15, pady=5)

# --- Dynamic Prompt Update & Main Loop ---
def update_prompt(*_):
    selected_scraper = scraper_type.get()
    prompt_label.configure(text=SCRAPER_MAP[selected_scraper]["prompt"])
    example_label.configure(text=SCRAPER_MAP[selected_scraper]["example"])
    input_var.set("")
    output_box.configure(state="normal")
    output_box.delete("1.0", "end")
    output_box.configure(state="disabled")
    exec_label.configure(text="")
    message_label.configure(text="", text_color=TEXT_COLOR)
    input_entry.configure(border_color=DEFAULT_BORDER_COLOR) # Reset border color on scraper type change

scraper_type.trace("w", update_prompt)
app.bind("<Escape>", lambda e: app.destroy())

# Ensure all widgets are rendered to get accurate positions for scrolling
# This will also trigger the initial resize_logo via the <Configure> binding
app.update_idletasks()
app.mainloop()