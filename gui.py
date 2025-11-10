# gui.py
"""
Simple Tkinter GUI for the face attendance system.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from register import register_user
from train import train
from attendance import attend
from db import fetch_attendance, init_db

# ensure DB/tables exist
init_db()

def run_register(user_id, name, email, samples=30 ):
    try:
        cnt = register_user(user_id, name, email, samples)
        messagebox.showinfo("Done", f"Captured {cnt} images for {name}.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def on_register_click():
    uid = entry_id.get().strip()
    name = entry_name.get().strip()
    email = entry_email.get().strip()
    if not uid or not name or not email:
        messagebox.showwarning("Missing", "Please enter ID, Name, and Email.")
        return
    # run in a thread so GUI doesn't freeze
    threading.Thread(target=run_register, args=(uid, name, email, 30), daemon=True).start()

def on_train_click():
    def _train():
        try:
            train()
            messagebox.showinfo("Trained", "Training complete.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    threading.Thread(target=_train, daemon=True).start()

def on_attend_click():
    def _attend():
        try:
            attend()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    threading.Thread(target=_attend, daemon=True).start()

def on_view_click():
    rows = fetch_attendance(200)
    text.delete("1.0", tk.END)
    for r in rows:
        text.insert(tk.END, f"{r['login_time']} | {r['user_id']} | {r.get('name','-')} | {r.get('email','-')} | {r['status']}\n")

root = tk.Tk()
root.title("Face Recognition Attendance")

frm = ttk.Frame(root, padding=12)
frm.grid()

ttk.Label(frm, text="User ID:").grid(column=0, row=0, sticky=tk.W)
entry_id = ttk.Entry(frm, width=30)
entry_id.grid(column=1, row=0)

ttk.Label(frm, text="Name:").grid(column=0, row=1, sticky=tk.W)
entry_name = ttk.Entry(frm, width=30)
entry_name.grid(column=1, row=1)

ttk.Label(frm, text="Email:").grid(column=0, row=2, sticky=tk.W)
entry_email = ttk.Entry(frm, width=30)
entry_email.grid(column=1, row=2)

btn_register = ttk.Button(frm, text="Register User (Capture Faces)", command=on_register_click)
btn_register.grid(column=0, row=3, columnspan=2, pady=(8,0), sticky=tk.EW)

btn_train = ttk.Button(frm, text="Train Faces", command=on_train_click)
btn_train.grid(column=0, row=4, columnspan=2, pady=(6,0), sticky=tk.EW)

btn_attend = ttk.Button(frm, text="Take Attendance (Live)", command=on_attend_click)
btn_attend.grid(column=0, row=5, columnspan=2, pady=(6,0), sticky=tk.EW)

btn_view = ttk.Button(frm, text="View Attendance (Last 200)", command=on_view_click)
btn_view.grid(column=0, row=6, columnspan=2, pady=(6,0), sticky=tk.EW)

text = tk.Text(root, width=80, height=12)
text.grid(padx=12, pady=12)

root.mainloop()
