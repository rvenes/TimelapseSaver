import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import requests
import os

class TimelapseSaver:
    def __init__(self, root):
        self.root = root
        self.root.title("TimelapseSaver")

        # Default configuration
        self.image_url = "http://10.0.0.81/snap.jpeg"
        self.save_path = os.getcwd()
        self.interval = 3600  # Default to 1 image per hour
        self.running = False

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

        tk.Button(root, text="Test", command=self.test_capture).grid(row=4, column=0, padx=5, pady=10)

        tk.Button(root, text="Exit", command=root.quit).grid(row=4, column=1, padx=5, pady=10)

    def browse_directory(self):
        selected_path = filedialog.askdirectory(initialdir=self.save_path)
        if selected_path:
            self.save_path = selected_path
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, self.save_path)

    def test_capture(self):
        try:
            response = requests.get(self.url_entry.get(), stream=True)
            response.raise_for_status()
            test_image_path = os.path.join(self.save_path, "test_image.jpeg")
            with open(test_image_path, "wb") as f:
                f.write(response.content)
            messagebox.showinfo("Success", f"Test image saved to {test_image_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture test image: {e}")

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
            messagebox.showerror("Error", f"Failed to start capturing: {e}")

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
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                image_path = os.path.join(self.save_path, f"image_{timestamp}.jpeg")
                with open(image_path, "wb") as f:
                    f.write(response.content)
                image_count += 1
            except Exception as e:
                messagebox.showerror("Error", f"Failed to capture image: {e}")
            time.sleep(self.interval)

if __name__ == "__main__":
    root = tk.Tk()
    app = TimelapseSaver(root)
    root.mainloop()
