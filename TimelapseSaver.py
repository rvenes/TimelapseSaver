import tkinter as tk
from tkinter import filedialog, Menu, Toplevel
from PIL import Image, ImageTk
import threading
import time
import requests
import os
import webbrowser
import io
from datetime import datetime

VERSION = "1.0.2"

class TimelapseSaver:
    def __init__(self, root):
        self.root = root
        self.root.title(f"TimelapseSaver v{VERSION}")

        # Default configuration
        self.image_url = "http://10.0.0.81/snap.jpeg"
        self.save_path = os.getcwd()
        self.interval = 60  # Default to 60 seconds
        self.running = False
        self.original_image = None
        self.popup_window = None

        # Menu
        menubar = Menu(self.root)

        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="Changelog", command=self.show_changelog)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

        # GUI Elements
        tk.Label(root, text="Image URL:").grid(row=0, column=0, sticky="e")
        self.url_entry = tk.Entry(root, width=40)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)
        self.url_entry.insert(0, self.image_url)

        tk.Label(root, text="Save Directory:").grid(row=1, column=0, sticky="e")
        self.path_entry = tk.Entry(root, width=40)
        self.path_entry.grid(row=1, column=1, padx=5, pady=5)
        self.path_entry.insert(0, self.save_path)
        tk.Button(root, text="Browse", command=self.browse_directory).grid(row=1, column=2, padx=5, pady=5)

        tk.Label(root, text="Interval (seconds):").grid(row=2, column=0, sticky="e")
        self.interval_entry = tk.Entry(root, width=10)
        self.interval_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.interval_entry.insert(0, str(self.interval))

        self.start_button = tk.Button(root, text="Start", command=self.start_capture)
        self.start_button.grid(row=3, column=0, padx=5, pady=10)

        self.stop_button = tk.Button(root, text="Stop", command=self.stop_capture, state=tk.DISABLED)
        self.stop_button.grid(row=3, column=1, padx=5, pady=10)

        self.load_button = tk.Button(root, text="Load Picture", command=self.load_picture)
        self.load_button.grid(row=4, column=0, padx=5, pady=10)

        tk.Button(root, text="Exit", command=root.quit).grid(row=4, column=1, padx=5, pady=10)

        self.image_label = tk.Label(root, cursor="hand2")
        self.image_label.grid(row=5, column=0, columnspan=3, pady=10)
        self.image_label.bind("<Button-1>", self.show_popup_image)

        self.info_label = tk.Label(root, text="", justify="left")
        self.info_label.grid(row=6, column=0, columnspan=3, pady=10)

    def browse_directory(self):
        selected_path = filedialog.askdirectory(initialdir=self.save_path)
        if selected_path:
            self.save_path = selected_path
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, self.save_path)

    def load_picture(self):
        try:
            response = requests.get(self.url_entry.get(), stream=True)
            response.raise_for_status()
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))

            # Store the original image
            self.original_image = image.copy()

            # Resize for display
            original_size = image.size
            image.thumbnail((640, 360))

            # Convert to Tkinter-compatible image
            tk_image = ImageTk.PhotoImage(image)
            self.image_label.config(image=tk_image)
            self.image_label.image = tk_image

            # Update info label
            size_kb = len(image_data) / 1024
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.info_label.config(
                text=(
                    f"Image Info:\n"
                    f"- Original Size: {original_size[0]}x{original_size[1]} px\n"
                    f"- Displayed Size: {image.width}x{image.height} px\n"
                    f"- File Size: {size_kb:.2f} KB\n"
                    f"- Loaded At: {timestamp}"
                )
            )

            # Change button text to Reload
            self.load_button.config(text="Reload Picture")

        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to load picture: {e}")

    def show_popup_image(self, event):
        if self.original_image:
            if self.popup_window and self.popup_window.winfo_exists():
                self.popup_window.destroy()
            else:
                self.popup_window = Toplevel(self.root)
                self.popup_window.title("Full Image")
                tk_image = ImageTk.PhotoImage(self.original_image)
                label = tk.Label(self.popup_window, image=tk_image)
                label.image = tk_image
                label.pack()

    def start_capture(self):
        try:
            self.image_url = self.url_entry.get()
            self.save_path = self.path_entry.get()
            self.interval = int(self.interval_entry.get())

            if not os.path.exists(self.save_path):
                raise ValueError("Invalid save directory")

            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)

            self.capture_thread = threading.Thread(target=self.capture_images)
            self.capture_thread.daemon = True
            self.capture_thread.start()

        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to start capturing: {e}")

    def stop_capture(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def capture_images(self):
        image_count = 0
        while self.running:
            try:
                response = requests.get(self.image_url, stream=True)
                response.raise_for_status()
                timestamp = time.strftime("%Y%m%d_%H%M:%S")
                image_path = os.path.join(self.save_path, f"image_{timestamp}.jpeg")
                with open(image_path, "wb") as f:
                    f.write(response.content)
                image_count += 1
            except Exception as e:
                tk.messagebox.showerror("Error", f"Failed to capture image: {e}")
            time.sleep(self.interval)

    def show_about(self):
        about_frame = Toplevel(self.root)
        about_frame.title("About")

        tk.Label(about_frame, text=f"TimelapseSaver v{VERSION}\n\nThis application is licensed under the GNU General Public License.", wraplength=400, justify="left").pack(pady=5)
        tk.Label(about_frame, text="If you would like to support development, you are welcome to donate:", wraplength=400, justify="left").pack(pady=5)

        tk.Button(about_frame, text="Donate via PayPal", fg="blue", cursor="hand2", command=lambda: webbrowser.open("https://paypal.me/rvenes?country.x=NO&locale.x=en_US")).pack(pady=5)

        bitcoin_frame = tk.Frame(about_frame)
        bitcoin_label = tk.Label(bitcoin_frame, text="Bitcoin: 3CEUbAnKZk3qLCARe5eDjq9sDgnZDZY4jg", wraplength=400, justify="left")
        bitcoin_label.pack(side=tk.LEFT, padx=5)
        tk.Button(bitcoin_frame, text="Copy", command=lambda: self.copy_to_clipboard("3CEUbAnKZk3qLCARe5eDjq9sDgnZDZY4jg")).pack(side=tk.RIGHT)
        bitcoin_frame.pack(pady=5)

        tk.Button(about_frame, text="Close", command=about_frame.destroy).pack(pady=10)

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

    def show_changelog(self):
        changelog = (
            "Changelog:\n"
            "- Version 1.0.2:\n"
            "  - Added \"Load Picture\" with EXIF display and resize.\n"
            "  - Full image popup with click functionality.\n"
            "  - About and Changelog in Help menu.\n"
            "  - Copy Bitcoin address and clickable PayPal link in About."
        )
        tk.messagebox.showinfo("Changelog", changelog)

if __name__ == "__main__":
    root = tk.Tk()
    app = TimelapseSaver(root)
    root.mainloop()
