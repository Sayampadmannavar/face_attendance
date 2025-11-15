# gui.py
"""
Simple Tkinter GUI for the face recognition attendance system.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from register import register_user
from train import train
from attendance import attend
from db import fetch_attendance, init_db

# Ensure DB/tables exist
init_db()

def run_register(user_id, name, email, samples=30):
    """Handles user registration with error handling for duplicates and other exceptions."""
    try:
        cnt = register_user(user_id, name, email, samples)
        messagebox.showinfo("Registration Complete", f"Captured {cnt} images for {name}.")
    except ValueError as ve:
        # Handles duplicate face or email errors specifically
        msg = str(ve)
        if "email" in msg.lower():
            messagebox.showwarning("Duplicate Email", msg)
        elif "face" in msg.lower():
            messagebox.showwarning("Duplicate Face", msg)
        else:
            messagebox.showwarning("Warning", msg)
    except Exception as e:
        # Handles unexpected errors
        messagebox.showerror("Error", f"Unexpected error: {str(e)}")

def on_register_click():
    uid = entry_id.get().strip()
    name = entry_name.get().strip()
    email = entry_email.get().strip()

    if not uid or not name or not email:
        messagebox.showwarning("Missing Information", "Please enter ID, Name, and Email before registering.")
        return

    # Run in a separate thread so GUI doesn’t freeze
    threading.Thread(target=run_register, args=(uid, name, email, 30), daemon=True).start()

def on_train_click():
    """Handles the 'Train Faces' button click event."""
    def _train():
        try:
            train()
            messagebox.showinfo("Training Complete", "Face recognition model has been trained successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Training failed: {str(e)}")
    threading.Thread(target=_train, daemon=True).start()

def on_attend_click():
    """Handles the 'Take Attendance' button click event."""
    def _attend():
        try:
            attend()
        except Exception as e:
            messagebox.showerror("Error", f"Attendance failed: {str(e)}")
    threading.Thread(target=_attend, daemon=True).start()

def on_view_click():
    """Handles the 'View Attendance' button click event."""
    rows = fetch_attendance(200)
    text.delete("1.0", tk.END)
    for r in rows:
        text.insert(
            tk.END,
            f"{r['login_time']} | {r['user_id']} | {r.get('name','-')} | {r.get('email','-')} | {r['status']}\n"
        )

# ---------------- GUI Layout ---------------- #

root = tk.Tk()
root.title("Face Recognition Attendance System")

frm = ttk.Frame(root, padding=12)
frm.grid()

# User input fields
ttk.Label(frm, text="User ID:").grid(column=0, row=0, sticky=tk.W)
entry_id = ttk.Entry(frm, width=30)
entry_id.grid(column=1, row=0)

ttk.Label(frm, text="Name:").grid(column=0, row=1, sticky=tk.W)
entry_name = ttk.Entry(frm, width=30)
entry_name.grid(column=1, row=1)

ttk.Label(frm, text="Email:").grid(column=0, row=2, sticky=tk.W)
entry_email = ttk.Entry(frm, width=30)
entry_email.grid(column=1, row=2)

# Buttons
btn_register = ttk.Button(frm, text="Register User (Capture Faces)", command=on_register_click)
btn_register.grid(column=0, row=3, columnspan=2, pady=(8, 0), sticky=tk.EW)

btn_train = ttk.Button(frm, text="Train Faces", command=on_train_click)
btn_train.grid(column=0, row=4, columnspan=2, pady=(6, 0), sticky=tk.EW)

btn_attend = ttk.Button(frm, text="Take Attendance (Live)", command=on_attend_click)
btn_attend.grid(column=0, row=5, columnspan=2, pady=(6, 0), sticky=tk.EW)

btn_view = ttk.Button(frm, text="View Attendance (Last 200)", command=on_view_click)
btn_view.grid(column=0, row=6, columnspan=2, pady=(6, 0), sticky=tk.EW)

# Text box for attendance logs
text = tk.Text(root, width=80, height=12)
text.grid(padx=12, pady=12)

root.mainloop()
