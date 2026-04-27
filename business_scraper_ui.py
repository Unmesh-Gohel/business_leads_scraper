import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from datetime import datetime

from scraper_core import (
    METERS_PER_MILE,
    parse_batch_file,
    parse_batch_lines,
    run_batch_scrape,
    scrape_keyword_zip,
    write_rows_to_csv,
)


def run_query():
    api_key = api_key_entry.get().strip()
    business_type = business_type_entry.get().strip()
    zip_code = zip_entry.get().strip()
    custom_filename = file_name_entry.get().strip()

    try:
        radius_miles = float(radius_entry.get().strip())
    except ValueError:
        messagebox.showerror("Invalid Input", "Search radius must be a number (miles).")
        return

    if radius_miles <= 0:
        messagebox.showerror("Invalid Input", "Search radius must be greater than 0 miles.")
        return
    radius_meters = int(radius_miles * METERS_PER_MILE)

    if not api_key or not business_type or not zip_code:
        messagebox.showerror(
            "Missing Input",
            "Please fill in the API Key, Business Type, and Zip Code fields.",
        )
        return

    try:
        rows = scrape_keyword_zip(api_key, business_type, zip_code, radius_meters)
    except Exception as exc:
        messagebox.showerror("Error", str(exc))
        return

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if custom_filename == "":
        csv_filename = f"{business_type}_{zip_code}_{timestamp}.csv"
    else:
        csv_filename = f"{custom_filename}_{timestamp}.csv"

    write_rows_to_csv(csv_filename, rows)

    messagebox.showinfo("Success", f"Data successfully saved to {csv_filename}")


def load_batch_file():
    file_path = filedialog.askopenfilename(
        title="Select batch input file",
        filetypes=[
            ("Text and CSV files", "*.txt *.csv"),
            ("Text files", "*.txt"),
            ("CSV files", "*.csv"),
            ("All files", "*.*"),
        ],
    )
    if not file_path:
        return

    try:
        pairs = parse_batch_file(file_path)
    except Exception as exc:
        messagebox.showerror("Load Error", str(exc))
        return

    if not pairs:
        messagebox.showerror("Load Error", "No valid batch rows found in file.")
        return

    batch_text.delete("1.0", tk.END)
    batch_text.insert(tk.END, "\n".join(f"{keyword}|{zip_code}" for keyword, zip_code in pairs))
    messagebox.showinfo("Loaded", f"Loaded {len(pairs)} batch item(s).")


def run_batch():
    api_key = api_key_entry.get().strip()
    custom_filename = file_name_entry.get().strip()
    raw_batch = batch_text.get("1.0", tk.END).strip()

    try:
        radius_miles = float(radius_entry.get().strip())
    except ValueError:
        messagebox.showerror("Invalid Input", "Search radius must be a number (miles).")
        return

    if radius_miles <= 0:
        messagebox.showerror("Invalid Input", "Search radius must be greater than 0 miles.")
        return

    if not api_key:
        messagebox.showerror("Missing Input", "Please fill in the API Key field.")
        return
    if not raw_batch:
        messagebox.showerror("Missing Input", "Please add batch lines before running batch mode.")
        return

    try:
        batch_pairs = parse_batch_lines(raw_batch)
    except ValueError as exc:
        messagebox.showerror("Batch Format Error", str(exc))
        return

    try:
        csv_filename, row_count, errors = run_batch_scrape(
            api_key,
            batch_pairs,
            radius_miles,
            output_path=None,
            custom_filename=custom_filename,
        )
    except RuntimeError as exc:
        messagebox.showerror("Batch Failed", str(exc))
        return
    except Exception as exc:
        messagebox.showerror("Error", str(exc))
        return

    if errors:
        messagebox.showwarning(
            "Batch Completed with Errors",
            f"Saved {row_count} rows to {csv_filename}.\n"
            f"{len(errors)} batch item(s) failed.\n\n"
            + "\n".join(errors[:10]),
        )
    else:
        messagebox.showinfo("Batch Success", f"Saved {row_count} rows to {csv_filename}")


root = tk.Tk()
root.title("Business Scraper Tool")

tk.Label(root, text="API Key:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
api_key_entry = tk.Entry(root, width=50)
api_key_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(root, text="Business Type (Keyword):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
business_type_entry = tk.Entry(root, width=50)
business_type_entry.grid(row=1, column=1, padx=5, pady=5)

tk.Label(root, text="Zip Code:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
zip_entry = tk.Entry(root, width=50)
zip_entry.grid(row=2, column=1, padx=5, pady=5)

tk.Label(root, text="Search Radius (miles):").grid(row=3, column=0, sticky="e", padx=5, pady=5)
radius_entry = tk.Entry(root, width=50)
radius_entry.grid(row=3, column=1, padx=5, pady=5)

tk.Label(root, text="Custom File Name (optional):").grid(row=4, column=0, sticky="e", padx=5, pady=5)
file_name_entry = tk.Entry(root, width=50)
file_name_entry.grid(row=4, column=1, padx=5, pady=5)

run_button = tk.Button(root, text="Run Query", command=run_query)
run_button.grid(row=5, column=0, columnspan=2, pady=10)

tk.Label(
    root,
    text="Batch Mode (one per line: keyword|zip, e.g. realtor|10001):",
).grid(row=6, column=0, sticky="ne", padx=5, pady=5)
batch_text = scrolledtext.ScrolledText(root, width=50, height=8)
batch_text.grid(row=6, column=1, padx=5, pady=5)

load_button = tk.Button(root, text="Load Batch File (.txt/.csv)", command=load_batch_file)
load_button.grid(row=7, column=0, columnspan=2, pady=5)

batch_button = tk.Button(root, text="Run Batch", command=run_batch)
batch_button.grid(row=8, column=0, columnspan=2, pady=10)

root.mainloop()
