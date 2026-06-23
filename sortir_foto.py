import os
import shutil
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from exif import Image as ExifImage

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ProPhotoSorter(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("D-Sorter — Professional Photo Culler")
        self.geometry("1200x800")
        
        self.source_dir = ""
        self.photo_list = []
        self.current_index = 0
        self.zoom_factor = 1.0
        
        self.raw_image = None
        self.cached_preview = None
        
        # Konfigurasi Folder Tujuan Default
        self.folder_map = {
            "1": "1_Accept",
            "2": "2_Medium",
            "3": "3_Portfolio",
            "4": "4_Review",
            "5": "5_Trash"
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        # Menggunakan Grid Layout Utama: Kolom 0 (Sidebar), Kolom 1 (Main Preview)
        self.grid_columnconfigure(0, weight=0, minsize=280)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # ================= SIDEBAR PANEL (KIRI) =================
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color="#1e1e1e")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        # Tombol Load
        self.btn_load = ctk.CTkButton(self.sidebar, text="Load Images Folder", fg_color="#2b2b2b", hover_color="#3a3a3a", command=self.load_folder, font=("Segoe UI", 12, "bold"))
        self.btn_load.pack(fill="x", padx=15, pady=(20, 5))
        
        self.label_path = ctk.CTkLabel(self.sidebar, text="No folder selected", font=("Segoe UI", 11, "italic"), text_color="gray", wraplength=250)
        self.label_path.pack(fill="x", padx=15, pady=5)
        
        # Divider Line
        ctk.CTkFrame(self.sidebar, height=2, fg_color="#2d2d2d").pack(fill="x", padx=10, pady=10)
        
        # Target Folders Info
        ctk.CTkLabel(self.sidebar, text="🎯 TARGET DESTINATIONS", font=("Segoe UI", 11, "bold"), text_color="#3498db").pack(anchor="w", padx=15, pady=5)
        for key, folder in self.folder_map.items():
            lbl = ctk.CTkLabel(self.sidebar, text=f"[{key}]  ->  {folder}", font=("Segoe UI", 11), anchor="w")
            lbl.pack(fill="x", padx=20, pady=2)
            
        ctk.CTkFrame(self.sidebar, height=2, fg_color="#2d2d2d").pack(fill="x", padx=10, pady=10)
        
        # METADATA PANEL
        ctk.CTkLabel(self.sidebar, text="📊 METADATA INFO", font=("Segoe UI", 11, "bold"), text_color="#e67e22").pack(anchor="w", padx=15, pady=5)
        
        self.meta_filename = ctk.CTkLabel(self.sidebar, text="File: --", font=("Segoe UI", 12, "bold"), anchor="w", text_color="#f1c40f")
        self.meta_filename.pack(fill="x", padx=15, pady=2)
        
        self.meta_date = ctk.CTkLabel(self.sidebar, text="Date: --", font=("Segoe UI", 11), anchor="w")
        self.meta_date.pack(fill="x", padx=15, pady=2)
        
        self.meta_res = ctk.CTkLabel(self.sidebar, text="Resolution: --", font=("Segoe UI", 11), anchor="w")
        self.meta_res.pack(fill="x", padx=15, pady=2)
        
        self.meta_camera = ctk.CTkLabel(self.sidebar, text="Camera: --", font=("Segoe UI", 11), anchor="w")
        self.meta_camera.pack(fill="x", padx=15, pady=2)
        
        self.meta_exif = ctk.CTkLabel(self.sidebar, text="Specs: --", font=("Segoe UI", 11), anchor="w", text_color="#2ecc71")
        self.meta_exif.pack(fill="x", padx=15, pady=2)
        
        # Divider Line Sebelum Tombol Skip
        ctk.CTkFrame(self.sidebar, height=2, fg_color="#2d2d2d").pack(fill="x", padx=10, pady=15)
        
        # TOMBOL SKIP FISIK (DI SIDEBAR)
        self.btn_skip = ctk.CTkButton(self.sidebar, text="➡️ Skip Image [Spasi]", fg_color="#e67e22", hover_color="#d35400", command=self.next_photo, font=("Segoe UI", 12, "bold"))
        self.btn_skip.pack(fill="x", padx=15, pady=5, ipady=4)
        
        # Hint Bawah Sidebar
        self.label_tip = ctk.CTkLabel(self.sidebar, text="⌨️ Keyboard Shortcut:\nTekan Angka 1-5 untuk sortir\nTekan Spasi untuk Lewati", font=("Segoe UI", 11), text_color="gray", justify="left")
        self.label_tip.pack(side="bottom", padx=15, pady=20, fill="x")

        # ================= MAIN AREA (KANAN) =================
        self.main_area = ctk.CTkFrame(self, fg_color="#121212", corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew")
        
        # Top Shortcut Bar (Indikator Angka ala Pxgate)
        self.frame_indicators = ctk.CTkFrame(self.main_area, fg_color="transparent", height=50)
        self.frame_indicators.pack(fill="x", pady=(15, 5))
        
        self.ind_buttons = {}
        for i in range(1, 6):
            btn = ctk.CTkLabel(self.frame_indicators, text=str(i), font=("Impact", 22, "italic"), width=50, height=40, fg_color="#1c1c1c", text_color="#444444", corner_radius=6)
            btn.pack(side="left", padx=5, expand=True)
            self.ind_buttons[str(i)] = btn

        # Canvas Preview Utama
        self.canvas_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.canvas_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.canvas = ctk.CTkCanvas(self.canvas_frame, bg="#151515", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Bindings Mouse & Keyboard
        self.canvas.bind("<MouseWheel>", self.zoom_image)
        self.bind("1", lambda e: self.move_photo("1"))
        self.bind("2", lambda e: self.move_photo("2"))
        self.bind("3", lambda e: self.move_photo("3"))
        self.bind("4", lambda e: self.move_photo("4"))
        self.bind("5", lambda e: self.move_photo("5"))
        self.bind("<space>", lambda e: self.next_photo())
        
        # Bar Progress Bawah
        self.label_counter = ctk.CTkLabel(self.main_area, text="Images: 0 / 0", font=("Segoe UI", 12, "bold"))
        self.label_counter.pack(pady=(0, 15))

    def load_folder(self):
        self.source_dir = filedialog.askdirectory()
        if not self.source_dir:
            return
            
        self.label_path.configure(text=self.source_dir)
        extensions = ('.jpg', '.jpeg', '.png', '.arw', '.cr2', '.nef')
        self.photo_list = [f for f in os.listdir(self.source_dir) if f.lower().endswith(extensions)]
        self.current_index = 0
        
        if self.photo_list:
            self.show_photo()
        else:
            messagebox.showinfo("Empty", "No compatible images found.")

    def show_photo(self):
        if self.current_index >= len(self.photo_list):
            messagebox.showinfo("Done", "All images processed!")
            self.canvas.delete("all")
            self.label_counter.configure(text="IMAGE 0 OF 0")
            return
            
        self.zoom_factor = 1.0
        filename = self.photo_list[self.current_index]
        self.label_counter.configure(text=f"IMAGE {self.current_index + 1} OF {len(self.photo_list)}")
        
        file_path = os.path.join(self.source_dir, filename)
        
        self.read_metadata(file_path, filename)
        
        try:
            with Image.open(file_path) as img_raw:
                img_copy = img_raw.copy()
                img_copy.thumbnail((1600, 1600), Image.Resampling.NEAREST)
                self.cached_preview = img_copy
                
            self.render_image()
        except Exception:
            self.canvas.delete("all")
            self.canvas.create_text(400, 300, text="Failed to render preview", fill="white")

    def read_metadata(self, file_path, filename):
        self.meta_filename.configure(text=f"File: {filename}")
        self.meta_date.configure(text="Date: --")
        self.meta_res.configure(text="Resolution: --")
        self.meta_camera.configure(text="Camera: --")
        self.meta_exif.configure(text="Specs: --")
        
        try:
            with Image.open(file_path) as img:
                w, h = img.size
                self.meta_res.configure(text=f"Res: {w} x {h} px")
            
            with open(file_path, 'rb') as img_file:
                file_bytes = img_file.read()
                my_image = ExifImage(file_bytes)
                
            if my_image.has_exif:
                cam_model = my_image.get("model", "Unknown Camera")
                date_taken = my_image.get("datetime_original", "--")
                
                shutter = my_image.get("exposure_time", "")
                aperture = my_image.get("f_number", "")
                iso = my_image.get("iso_speed_ratings", "")
                
                if shutter and shutter < 1.0:
                    shutter_str = f"1/{int(1/shutter)}s"
                else:
                    shutter_str = f"{shutter}s" if shutter else "--"
                    
                aperture_str = f"f/{aperture}" if aperture else "--"
                iso_str = f"ISO {iso}" if iso else "--"
                
                self.meta_camera.configure(text=f"Cam: {cam_model}")
                self.meta_date.configure(text=f"Date: {date_taken}")
                self.meta_exif.configure(text=f"⏱️ {shutter_str}  |  ⭕ {aperture_str}  |  🎞️ {iso_str}")
        except Exception:
            pass

    def render_image(self):
        if not self.cached_preview:
            return
            
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw <= 1: cw = 880
        if ch <= 600: ch = 600

        iw, ih = self.cached_preview.size
        ratio = min(cw / iw, ch / ih)
        
        nw = int(iw * ratio * self.zoom_factor)
        nh = int(ih * ratio * self.zoom_factor)
        
        resample_mode = Image.Resampling.LANCZOS if self.zoom_factor == 1.0 else Image.Resampling.BILINEAR
        
        resized = self.cached_preview.resize((nw, nh), resample_mode)
        self.photo_tk = ImageTk.PhotoImage(resized)
        
        self.canvas.delete("all")
        self.canvas.create_image(cw / 2, ch / 2, anchor="center", image=self.photo_tk)

    def zoom_image(self, event):
        if event.delta > 0:
            self.zoom_factor *= 1.25
        else:
            self.zoom_factor /= 1.25
            
        self.zoom_factor = max(0.5, min(self.zoom_factor, 6.0))
        self.render_image()

    def move_photo(self, rating_key):
        if self.current_index >= len(self.photo_list):
            return
            
        self.flash_indicator(rating_key)
        
        filename = self.photo_list[self.current_index]
        src = os.path.join(self.source_dir, filename)
        
        target_subfolder = self.folder_map[rating_key]
        dest_dir = os.path.join(self.source_dir, target_subfolder)
        
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
            
        try:
            shutil.move(src, os.path.join(dest_dir, filename))
            self.photo_list.pop(self.current_index)
            self.show_photo()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def flash_indicator(self, key):
        colors = {"1": "#2ecc71", "2": "#3498db", "3": "#9b59b6", "4": "#f1c40f", "5": "#e74c3c"}
        self.ind_buttons[key].configure(fg_color=colors[key], text_color="white")
        self.after(150, lambda: self.ind_buttons[key].configure(fg_color="#1c1c1c", text_color="#444444"))

    def next_photo(self):
        if self.current_index < len(self.photo_list) - 1:
            self.current_index += 1
            self.show_photo()
        elif self.current_index == len(self.photo_list) - 1:
            messagebox.showinfo("End", "Ini adalah foto terakhir di folder ini.")

if __name__ == "__main__":
    app = ProPhotoSorter()
    app.after(200, lambda: app.render_image())
    app.mainloop()