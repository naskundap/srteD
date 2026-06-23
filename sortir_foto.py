<<<<<<< HEAD
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
=======
import os
import shutil
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from exif import Image as ExifImage
import pygame

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ProPhotoSorter(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("srteD — Professional Photo Culler")
        self.geometry("1280x850") 
        
        self.source_dir = ""
        self.photo_list = []
        self.current_index = 0
        self.zoom_factor = 1.0
        
        self.raw_image = None
        self.cached_preview = None
        self.history_stack = [] 
        
        self.folder_map = {
            "1": "1_Accept",
            "2": "2_Medium",
            "3": "3_Portfolio",
            "4": "4_Review",
            "5": "5_Trash"
        }
        
        self.controller_buttons_map = {
            "1": "A / ❌",
            "2": "B / ⭕",
            "3": "X / 🔲",
            "4": "Y / 🔺",
            "5": "RT / R2"
        }
        
        self.setup_ui()
        self.setup_controller()
        
    def setup_ui(self):
        # Master Grid Layout
        self.grid_columnconfigure(0, weight=0, minsize=320)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # ================= SIDEBAR PANEL (KIRI) =================
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=0, fg_color="#1e1e1e")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        # Konfigurasi baris grid internal di dalam sidebar
        self.sidebar.rowconfigure(0, weight=0)
        self.sidebar.rowconfigure(1, weight=0)
        self.sidebar.rowconfigure(2, weight=0)
        self.sidebar.rowconfigure(3, weight=0)
        self.sidebar.rowconfigure(4, weight=0)
        self.sidebar.rowconfigure(5, weight=0)
        self.sidebar.rowconfigure(6, weight=0)
        self.sidebar.rowconfigure(7, weight=0)
        self.sidebar.rowconfigure(8, weight=1) # Spacer pendorong karet ke bawah
        self.sidebar.rowconfigure(9, weight=0)
        self.sidebar.rowconfigure(10, weight=0)
        self.sidebar.rowconfigure(11, weight=0)
        
        # 0. Tombol Load Folder
        self.btn_load = ctk.CTkButton(self.sidebar, text="Load Images Folder", fg_color="#2b2b2b", hover_color="#3a3a3a", command=self.load_folder, font=("Segoe UI", 12, "bold"))
        self.btn_load.grid(row=0, column=0, sticky="ew", padx=15, pady=(20, 5))
        
        # 1. Path Label
        self.label_path = ctk.CTkLabel(self.sidebar, text="No folder selected", font=("Segoe UI", 11, "italic"), text_color="gray", wraplength=280, justify="left", anchor="w")
        self.label_path.grid(row=1, column=0, sticky="ew", padx=15, pady=2)
        
        # 2. Divider 1 (FIXED: Menggunakan sticky="ew", bukan fill)
        ctk.CTkFrame(self.sidebar, height=2, fg_color="#2d2d2d").grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        # 3. Title Destinations
        self.label_dest_title = ctk.CTkLabel(self.sidebar, text="🎯 TARGET DESTINATIONS", font=("Segoe UI", 11, "bold"), text_color="#3498db", anchor="w")
        self.label_dest_title.grid(row=3, column=0, sticky="ew", padx=15, pady=(2, 5))
        
        # 4. Destinations List Frame
        self.frame_dest_list = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_dest_list.grid(row=4, column=0, sticky="ew", padx=15, pady=0)
        
        self.dest_labels = {}
        for idx, (key, folder) in enumerate(self.folder_map.items()):
            lbl = ctk.CTkLabel(self.frame_dest_list, text=f"[{key}]  ->  {folder}", font=("Segoe UI", 11), anchor="w", justify="left")
            lbl.pack(fill="x", pady=2)
            self.dest_labels[key] = lbl
            
        # 5. Divider 2
        ctk.CTkFrame(self.sidebar, height=2, fg_color="#2d2d2d").grid(row=5, column=0, sticky="ew", padx=10, pady=10)
        
        # 6. Title Metadata
        ctk.CTkLabel(self.sidebar, text="📊 METADATA INFO", font=("Segoe UI", 11, "bold"), text_color="#e67e22", anchor="w").grid(row=6, column=0, sticky="ew", padx=15, pady=(2, 5))
        
        # 7. Metadata List Frame
        self.frame_meta_list = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_meta_list.grid(row=7, column=0, sticky="ew", padx=15, pady=0)
        
        self.meta_filename = ctk.CTkLabel(self.frame_meta_list, text="File: --", font=("Segoe UI", 11, "bold"), anchor="w", text_color="#f1c40f", wraplength=280, justify="left")
        self.meta_filename.pack(fill="x", pady=2)
        
        self.meta_date = ctk.CTkLabel(self.frame_meta_list, text="Date: --", font=("Segoe UI", 11), anchor="w", justify="left")
        self.meta_date.pack(fill="x", pady=2)
        
        self.meta_res = ctk.CTkLabel(self.frame_meta_list, text="Resolution: --", font=("Segoe UI", 11), anchor="w", justify="left")
        self.meta_res.pack(fill="x", pady=2)
        
        self.meta_camera = ctk.CTkLabel(self.frame_meta_list, text="Camera: --", font=("Segoe UI", 11), anchor="w", justify="left")
        self.meta_camera.pack(fill="x", pady=2)
        
        self.meta_exif = ctk.CTkLabel(self.frame_meta_list, text="Specs: --", font=("Segoe UI", 11, "bold"), anchor="w", text_color="#2ecc71", justify="left")
        self.meta_exif.pack(fill="x", pady=4)
        
        # 9. Frame Tombol Navigasi Bawah
        self.frame_nav_buttons = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_nav_buttons.grid(row=9, column=0, sticky="ew", padx=15, pady=(10, 5))
        
        self.btn_undo = ctk.CTkButton(self.frame_nav_buttons, text="↩️ Undo [⬅️]", fg_color="#c0392b", hover_color="#a93226", command=self.undo_photo, font=("Segoe UI", 11, "bold"))
        self.btn_undo.pack(side="left", expand=True, fill="x", padx=(0, 5), ipady=5)
        
        self.btn_skip = ctk.CTkButton(self.frame_nav_buttons, text="Next [➡️]", fg_color="#27ae60", hover_color="#218c53", command=self.next_photo, font=("Segoe UI", 11, "bold"))
        self.btn_skip.pack(side="right", expand=True, fill="x", padx=(5, 0), ipady=5)
        
        # 10. Hint Shortcut
        self.label_nav_hint = ctk.CTkLabel(self.sidebar, text="⌨️ Keyboard Shortcut:\nPanah Kanan = Skip | Panah Kiri = Undo", font=("Segoe UI", 10), text_color="gray", justify="left", anchor="w")
        self.label_nav_hint.grid(row=10, column=0, sticky="ew", padx=15, pady=5)
        
        # 11. Controller Status
        self.label_controller_status = ctk.CTkLabel(self.sidebar, text="🎮 Controller: Disconnected", font=("Segoe UI", 11, "bold"), text_color="#e74c3c")
        self.label_controller_status.grid(row=11, column=0, sticky="ew", padx=15, pady=15)

        # ================= MAIN AREA (KANAN) =================
        self.main_area = ctk.CTkFrame(self, fg_color="#121212", corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew")
        
        # FIXED INDICATORS TOP BAR: Dipastikan Center dan Tidak Terdistorsi
        self.frame_indicators = ctk.CTkFrame(self.main_area, fg_color="transparent", height=60)
        self.frame_indicators.pack(fill="x", pady=(20, 5))
        
        self.inner_ind_frame = ctk.CTkFrame(self.frame_indicators, fg_color="transparent")
        self.inner_ind_frame.pack(anchor="center")
        
        self.ind_buttons = {}
        for i in range(1, 6):
            btn = ctk.CTkLabel(self.inner_ind_frame, text=str(i), font=("Impact", 24, "italic"), width=60, height=45, fg_color="#1c1c1c", text_color="#444444", corner_radius=6)
            btn.grid(row=0, column=i-1, padx=8)
            self.ind_buttons[str(i)] = btn

        # Canvas Preview Utama
        self.canvas_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.canvas_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.canvas = ctk.CTkCanvas(self.canvas_frame, bg="#151515", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.canvas.bind("<MouseWheel>", self.zoom_image)
        
        # Bindings Keyboard
        self.bind("1", lambda e: self.move_photo("1"))
        self.bind("2", lambda e: self.move_photo("2"))
        self.bind("3", lambda e: self.move_photo("3"))
        self.bind("4", lambda e: self.move_photo("4"))
        self.bind("5", lambda e: self.move_photo("5"))
        self.bind("<space>", lambda e: self.next_photo())
        self.bind("<Right>", lambda e: self.next_photo())
        self.bind("<Left>", lambda e: self.undo_photo())
        
        self.label_counter = ctk.CTkLabel(self.main_area, text="Images: 0 / 0", font=("Segoe UI", 12, "bold"))
        self.label_counter.pack(pady=(0, 15))

        self.trigger_locked = False

    def setup_controller(self):
        pygame.init()
        pygame.joystick.init()
        self.joystick = None
        self.update_controller_ui(connected=False)
        self.poll_controller()

    def poll_controller(self):
        pygame.event.pump()
        if pygame.joystick.get_count() > 0:
            if not self.joystick:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                self.update_controller_ui(connected=True)
            
            # 1. Deteksi Tombol Reguler
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    btn_id = event.button
                    if btn_id == 0:   self.move_photo("1") # A / X
                    elif btn_id == 1: self.move_photo("2") # B / O
                    elif btn_id == 2: self.move_photo("3") # X / Kotak
                    elif btn_id == 3: self.move_photo("4") # Y / Segitiga
                    elif btn_id == 4: self.undo_photo()    # LB / L1
                    elif btn_id == 5: self.next_photo()    # RB / R1
            
            # 2. Deteksi Trigger RT / R2 (Axis) untuk Folder Trash
            try:
                num_axes = self.joystick.get_numaxes()
                if num_axes > 4:
                    rt_val = self.joystick.get_axis(4) if num_axes == 5 else self.joystick.get_axis(5)
                    
                    if rt_val > 0.5 and not self.trigger_locked:
                        self.move_photo("5") 
                        self.trigger_locked = True
                    elif rt_val < 0.1:
                        self.trigger_locked = False
            except Exception:
                pass
        else:
            if self.joystick:
                self.joystick = None
                self.update_controller_ui(connected=False)
        
        self.after(50, self.poll_controller)

    def update_controller_ui(self, connected):
        if connected:
            self.label_controller_status.configure(text=f"🎮 Connected: {self.joystick.get_name()[:14]}", text_color="#2ecc71")
            self.label_dest_title.configure(text="🎮 CONTROLLER DESTINATIONS", text_color="#2ecc71")
            self.label_nav_hint.configure(text="🕹️ Controller Shortcut:\nLB = Undo / Back | RB = Skip / Next", text_color="#2ecc71")
            self.btn_undo.configure(text="↩️ Undo [LB]")
            self.btn_skip.configure(text="Next [RB]")
            
            for key, folder in self.folder_map.items():
                btn_name = self.controller_buttons_map[key]
                self.dest_labels[key].configure(text=f"[{btn_name}] -> {folder}", text_color="#f1c40f")
        else:
            self.label_controller_status.configure(text="🎮 Controller: Disconnected", text_color="#e74c3c")
            self.label_dest_title.configure(text="🎯 TARGET DESTINATIONS", text_color="#3498db")
            self.label_nav_hint.configure(text="⌨️ Keyboard Shortcut:\nPanah Kanan = Skip | Panah Kiri = Undo", text_color="gray")
            self.btn_undo.configure(text="↩️ Undo [⬅️]")
            self.btn_skip.configure(text="Next [➡️]")
            
            for key, folder in self.folder_map.items():
                self.dest_labels[key].configure(text=f"[{key}]  ->  {folder}", text_color="white")

    def load_folder(self):
        self.source_dir = filedialog.askdirectory()
        if not self.source_dir:
            return
            
        self.label_path.configure(text=self.source_dir)
        extensions = ('.jpg', '.jpeg', '.png', '.arw', '.cr2', '.nef')
        self.photo_list = [f for f in os.listdir(self.source_dir) if f.lower().endswith(extensions)]
        self.current_index = 0
        self.history_stack.clear()
        
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
            
        if self.current_index < 0:
            self.current_index = 0
            
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
        if cw <= 1: cw = 950
        if ch <= 600: ch = 650

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
            
        dest_path = os.path.join(dest_dir, filename)
            
        try:
            shutil.move(src, dest_path)
            self.history_stack.append((filename, src, dest_path))
            self.photo_list.pop(self.current_index)
            self.show_photo()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def undo_photo(self):
        if self.history_stack:
            filename, original_src, current_dest = self.history_stack.pop()
            try:
                shutil.move(current_dest, original_src)
                self.photo_list.insert(self.current_index, filename)
                self.show_photo()
            except Exception as e:
                messagebox.showerror("Undo Error", f"Gagal mengembalikan file: {e}")
        else:
            if self.current_index > 0:
                self.current_index -= 1
                self.show_photo()

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
>>>>>>> d17aa70 (Initial Commit: Versi Final srteD dengan UI Grid Fix dan RT/R2 Trigger)
    app.mainloop()