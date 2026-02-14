import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import tkinter.font as tkfont
import threading
import time
import os
import sys
import json
import ctypes
from datetime import timedelta

# Configuration
CONFIG_FILE = "config_for_shutdown_timer.json"
DEFAULT_CONFIG = {
    "font_family": "Arial",
    "font_size": 12,
    "text_color": "#FFFFFF",
    "bg_color": "#000000",
    "opacity": 0.9,
    "auto_size": True,
    "overlay_position": (0, 0),
    "overlay_size": (400, 200),
    "last_timer": {"days": 0, "hours": 0, "minutes": 0, "seconds": 0}
}

class ShutdownTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Shutdown Timer")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize state
        self.countdown_thread = None
        self.is_running = False
        self.is_paused = False
        self.remaining_time = 0
        self.start_time = 0
        self.pause_time = 0
        self.shutdown_scheduled = False
        self.overlay = None
        
        # Load configuration
        self.config = self.load_config()
        self.setup_styles()
        
        # Create main UI
        self.create_main_window()
        
        # Create overlay window
        self.create_overlay()
        
        # Restore last timer values
        self.restore_last_timer()
    
    def load_config(self):
        """Load configuration from file if enabled or use defaults"""
        try:
            if hasattr(self, 'save_config_var') and self.save_config_var.get() and os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults to handle missing keys
                    for key, value in DEFAULT_CONFIG.items():
                        if key not in config:
                            config[key] = value
                    return config
        except Exception as e:
            print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """Save configuration to file if enabled"""
        try:
            if self.save_config_var.get():
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def setup_styles(self):
        """Setup application styles"""
        style = ttk.Style()
        
        # Light mode colors (default)
        bg_color = "#ffffff"
        fg_color = "#000000"
        button_bg = "#f0f0f0"
        button_hover = "#e0e0e0"
        entry_bg = "#ffffff"
        
        self.root.configure(bg=bg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color)
        style.configure("TButton", background=button_bg, foreground=fg_color)
        style.configure("TEntry", fieldbackground=entry_bg, foreground=fg_color)
    
    def create_main_window(self):
        """Create the main application window"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input fields for countdown
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(pady=10, fill=tk.X)
        
        self.day_var = tk.StringVar(value="0")
        self.hour_var = tk.StringVar(value="0")
        self.minute_var = tk.StringVar(value="0")
        self.second_var = tk.StringVar(value="0")
        
        # Day input
        ttk.Label(input_frame, text="Days:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        day_entry = ttk.Entry(input_frame, textvariable=self.day_var, width=5, font=("Arial", 12))
        day_entry.grid(row=0, column=1, padx=5, pady=5)
        day_entry.bind("<KeyRelease>", lambda e: self.validate_input(e, self.day_var))
        
        # Hour input
        ttk.Label(input_frame, text="Hours:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        hour_entry = ttk.Entry(input_frame, textvariable=self.hour_var, width=5, font=("Arial", 12))
        hour_entry.grid(row=0, column=3, padx=5, pady=5)
        hour_entry.bind("<KeyRelease>", lambda e: self.validate_input(e, self.hour_var))
        
        # Minute input
        ttk.Label(input_frame, text="Minutes:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        minute_entry = ttk.Entry(input_frame, textvariable=self.minute_var, width=5, font=("Arial", 12))
        minute_entry.grid(row=0, column=5, padx=5, pady=5)
        minute_entry.bind("<KeyRelease>", lambda e: self.validate_input(e, self.minute_var))
        
        # Second input
        ttk.Label(input_frame, text="Seconds:").grid(row=0, column=6, padx=5, pady=5, sticky=tk.W)
        second_entry = ttk.Entry(input_frame, textvariable=self.second_var, width=5, font=("Arial", 12))
        second_entry.grid(row=0, column=7, padx=5, pady=5)
        second_entry.bind("<KeyRelease>", lambda e: self.validate_input(e, self.second_var))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20, fill=tk.X)
        
        self.start_btn = ttk.Button(button_frame, text="Start Timer", command=self.start_timer, state=tk.NORMAL)
        self.start_btn.pack(side=tk.LEFT, padx=10, expand=True)
        
        self.pause_btn = ttk.Button(button_frame, text="Pause", command=self.pause_timer, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=10, expand=True)
        
        self.cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.cancel_timer, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=10, expand=True)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to start timer")
        ttk.Label(main_frame, textvariable=self.status_var, font=("Arial", 10)).pack(pady=10)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.pack(pady=10, fill=tk.X)
        
        # Customization controls frame (vertical layout)
        customization_frame = ttk.Frame(settings_frame)
        customization_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Color and opacity controls
        color_frame = ttk.Frame(customization_frame)
        color_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(color_frame, text="Text Color", command=self.choose_text_color).pack(side=tk.LEFT, padx=5)
        ttk.Button(color_frame, text="BG Color", command=self.choose_bg_color).pack(side=tk.LEFT, padx=5)
        ttk.Button(color_frame, text="Opacity", command=self.adjust_opacity).pack(side=tk.LEFT, padx=5)
        ttk.Button(color_frame, text="Font", command=self.choose_font).pack(side=tk.LEFT, padx=5)
        
        # Checkboxes frame (vertical layout)
        checkboxes_frame = ttk.Frame(settings_frame)
        checkboxes_frame.pack(fill=tk.X)
        
        self.show_overlay_var = tk.BooleanVar(value=True)
        overlay_btn = ttk.Checkbutton(checkboxes_frame, text="Show Floating Overlay", variable=self.show_overlay_var,
                                     command=self.toggle_overlay)
        overlay_btn.pack(anchor=tk.W, pady=2)
        
        self.dynamic_size_var = tk.BooleanVar(value=self.config.get("auto_size", True))
        dynamic_size_btn = ttk.Checkbutton(checkboxes_frame, text="Dynamic Size (Auto-fit)", 
                                          variable=self.dynamic_size_var, command=self.toggle_dynamic_size)
        dynamic_size_btn.pack(anchor=tk.W, pady=2)
        
        self.save_config_var = tk.BooleanVar(value=False)
        save_config_btn = ttk.Checkbutton(checkboxes_frame, text="Save settings to config_for_shutdown_timer.json", 
                                          variable=self.save_config_var)
        save_config_btn.pack(anchor=tk.W, pady=2)
        
        # Auto-save current timer values
        self.save_timer_settings()
    
    def create_overlay(self):
        """Create the floating overlay window with dynamic sizing"""
        self.overlay = tk.Toplevel(self.root)
        self.overlay.title("Shutdown Timer Overlay")
        
        # Calculate initial window size based on font
        font_obj = tkfont.Font(family=self.config["font_family"], size=self.config["font_size"], weight="bold")
        max_text = "99:99:99:99"  # Maximum expected time format (days:hours:minutes:seconds)
        text_width = font_obj.measure(max_text)
        text_height = font_obj.metrics('linespace')
        
        # Set initial window size with minimal padding
        padding = 5
        self.overlay.geometry(f"{text_width + padding}x{text_height + padding}+"
                             f"{self.config['overlay_position'][0]}+{self.config['overlay_position'][1]}")
        
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        self.overlay.attributes("-alpha", self.config["opacity"])
        
        # Set resizable based on dynamic size setting
        self.overlay.resizable(not self.config.get("auto_size", True), not self.config.get("auto_size", True))
        
        # Create frame with no padding to hug the label tightly
        self.overlay_frame = ttk.Frame(self.overlay)
        self.overlay_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Countdown display - centered
        self.overlay_time_var = tk.StringVar(value="00:00:00")
        self.overlay_label = ttk.Label(self.overlay_frame, textvariable=self.overlay_time_var,
                                     font=(self.config["font_family"], self.config["font_size"], "bold"))
        self.overlay_label.pack(fill=tk.BOTH, expand=True)
        
        # Drag functionality
        self.overlay.bind("<ButtonPress-1>", self.start_drag)
        self.overlay.bind("<B1-Motion>", self.drag_window)
        
        # Resize functionality - only if dynamic size is disabled
        if not self.config.get("auto_size", True):
            self.overlay.bind("<ButtonPress-3>", self.start_resize)
            self.overlay.bind("<B3-Motion>", self.resize_window)
        
        # Update colors
        self.update_overlay_colors()
        
        # Hide initially if configured
        if not self.show_overlay_var.get():
            self.overlay.withdraw()
    
    def start_drag(self, event):
        """Start drag operation for overlay"""
        self.x = event.x
        self.y = event.y
    
    def drag_window(self, event):
        """Drag window to new position"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.overlay.winfo_x() + deltax
        y = self.overlay.winfo_y() + deltay
        self.overlay.geometry(f"+{x}+{y}")
    
    def start_resize(self, event):
        """Start resize operation for overlay"""
        self.resize_x = event.x
        self.resize_y = event.y
        self.start_width = self.overlay.winfo_width()
        self.start_height = self.overlay.winfo_height()
    
    def resize_window(self, event):
        """Resize window"""
        deltax = event.x - self.resize_x
        deltay = event.y - self.resize_y
        new_width = max(200, self.start_width + deltax)
        new_height = max(100, self.start_height + deltay)
        self.overlay.geometry(f"{new_width}x{new_height}")
        
        # Adjust font size if auto-size enabled
        if self.config["auto_size"]:
            self.adjust_font_size(new_width, new_height)
    
    def adjust_font_size(self, width, height):
        """Adjust font size based on window dimensions"""
        max_font_size = min(width // 5, height // 3)
        if max_font_size != self.config["font_size"]:
            self.config["font_size"] = max_font_size
            self.overlay_label.configure(font=(self.config["font_family"], max_font_size, "bold"))
    
    def validate_input(self, event, var):
        """Validate input fields to accept only positive integers"""
        value = var.get()
        
        # Allow empty string
        if value == "":
            self.save_timer_settings()
            return
        
        if not value.isdigit():
            var.set(value[:-1])
            return
        
        if int(value) < 0:
            var.set("")
            return
        
        # Limit maximum values to reasonable numbers
        if var == self.day_var and int(value) > 365:
            var.set("365")
        elif var == self.hour_var and int(value) > 23:
            var.set("23")
        elif var == self.minute_var and int(value) > 59:
            var.set("59")
        elif var == self.second_var and int(value) > 59:
            var.set("59")
        
        self.save_timer_settings()
    
    def save_timer_settings(self):
        """Save current timer settings to config"""
        self.config["last_timer"] = {
            "days": int(self.day_var.get()) if self.day_var.get().strip() else 0,
            "hours": int(self.hour_var.get()) if self.hour_var.get().strip() else 0,
            "minutes": int(self.minute_var.get()) if self.minute_var.get().strip() else 0,
            "seconds": int(self.second_var.get()) if self.second_var.get().strip() else 0
        }
        self.save_config()
    
    def restore_last_timer(self):
        """Restore last used timer values"""
        last_timer = self.config["last_timer"]
        self.day_var.set(str(last_timer["days"]) if last_timer["days"] > 0 else "")
        self.hour_var.set(str(last_timer["hours"]) if last_timer["hours"] > 0 else "")
        self.minute_var.set(str(last_timer["minutes"]) if last_timer["minutes"] > 0 else "")
        self.second_var.set(str(last_timer["seconds"]) if last_timer["seconds"] > 0 else "")
    
    def start_timer(self):
        """Start the countdown timer"""
        # Calculate total seconds, handling empty fields as 0
        try:
            days = int(self.day_var.get()) if self.day_var.get().strip() else 0
            hours = int(self.hour_var.get()) if self.hour_var.get().strip() else 0
            minutes = int(self.minute_var.get()) if self.minute_var.get().strip() else 0
            seconds = int(self.second_var.get()) if self.second_var.get().strip() else 0
            
            total_seconds = (days * 86400 +
                            hours * 3600 +
                            minutes * 60 +
                            seconds)
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values")
            return
        
        if total_seconds <= 0:
            messagebox.showerror("Error", "Please enter a valid countdown time (greater than 0)")
            return
        
        if self.is_running:
            messagebox.showwarning("Warning", "A timer is already running")
            return
        
        # Start timer in new thread
        self.is_running = True
        self.is_paused = False
        self.remaining_time = total_seconds
        self.start_time = time.time()
        
        self.countdown_thread = threading.Thread(target=self.countdown_task, daemon=True)
        self.countdown_thread.start()
        
        # Update UI
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.NORMAL)
        self.status_var.set(f"Timer started for {self.format_time(total_seconds)}")
        
        # Show overlay if not visible
        if self.show_overlay_var.get() and self.overlay.winfo_viewable() == 0:
            self.overlay.deiconify()
    
    def pause_timer(self):
        """Pause or resume the countdown"""
        if self.is_paused:
            # Resume timer
            self.is_paused = False
            self.pause_btn.config(text="Pause")
            self.status_var.set("Timer resumed")
            self.start_time = time.time() - (self.pause_time - self.start_time)
        else:
            # Pause timer
            self.is_paused = True
            self.pause_btn.config(text="Resume")
            self.pause_time = time.time()
            self.status_var.set("Timer paused")
    
    def cancel_timer(self):
        """Cancel the countdown"""
        if messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel the timer?"):
            self.is_running = False
            self.is_paused = False
            self.shutdown_scheduled = False
            
            self.start_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED, text="Pause")
            self.cancel_btn.config(state=tk.DISABLED)
            
            self.status_var.set("Timer canceled")
            self.overlay_time_var.set("00:00:00")
    
    def countdown_task(self):
        """Background thread for countdown"""
        try:
            while self.is_running and self.remaining_time > 0:
                if not self.is_paused:
                    current_time = time.time()
                    elapsed = current_time - self.start_time
                    self.remaining_time = max(0, self.remaining_time - elapsed)
                    self.start_time = current_time
                    
                    # Update UI
                    self.overlay_time_var.set(self.format_time(self.remaining_time))
                    
                    # Adjust overlay size if dynamic sizing is enabled
                    if self.config["auto_size"]:
                        self.root.after(0, self.adjust_overlay_size)
                    
                    # Show warning before shutdown
                    if self.remaining_time <= 10 and not self.shutdown_scheduled:
                        self.shutdown_scheduled = True
                        self.root.after(0, self.show_shutdown_warning)
                    
                    time.sleep(1)
                else:
                    time.sleep(0.1)
            
            # Timer completed
            if self.remaining_time <= 0 and self.is_running:
                self.root.after(0, self.perform_shutdown)
        
        except Exception as e:
            print(f"Countdown error: {e}")
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
            self.is_running = False
    
    def format_time(self, seconds):
        """Format time in appropriate format based on remaining seconds (without leading zeros)"""
        delta = timedelta(seconds=seconds)
        total_seconds = int(delta.total_seconds())
        
        if total_seconds >= 86400:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60
            secs = total_seconds % 60
            return f"{days}:{hours:02d}:{minutes:02d}:{secs:02d}"
        elif total_seconds >= 3600:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            secs = total_seconds % 60
            return f"{hours}:{minutes:02d}:{secs:02d}"
        elif total_seconds >= 60:
            minutes = total_seconds // 60
            secs = total_seconds % 60
            return f"{minutes}:{secs:02d}"
        else:
            return f"{total_seconds} sec"
    
    def show_shutdown_warning(self):
        """Show warning before shutdown"""
        warning_window = tk.Toplevel(self.root)
        warning_window.title("Shutdown Warning")
        warning_window.geometry("400x150")
        warning_window.overrideredirect(True)
        warning_window.attributes("-topmost", True)
        warning_window.attributes("-alpha", 0.95)
        
        # Center window
        warning_window.update_idletasks()
        x = (warning_window.winfo_screenwidth() - warning_window.winfo_reqwidth()) // 2
        y = (warning_window.winfo_screenheight() - warning_window.winfo_reqheight()) // 2
        warning_window.geometry(f"+{x}+{y}")
        
        ttk.Label(warning_window, text="Shutdown in 10 seconds!", 
                 font=("Arial", 16, "bold")).pack(pady=20)
        
        btn_frame = ttk.Frame(warning_window)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Cancel Shutdown", command=lambda: [self.cancel_timer(), warning_window.destroy()]).pack()
    
    def perform_shutdown(self):
        """Perform safe shutdown of Windows"""
        try:
            self.status_var.set("Performing shutdown...")
            self.is_running = False
            
            # Flush pending operations
            self.save_config()
            
            # Perform shutdown
            os.system("shutdown /s /t 5")
            
        except Exception as e:
            print(f"Shutdown error: {e}")
            self.status_var.set(f"Shutdown error: {str(e)}")
    
    def choose_text_color(self):
        """Open color chooser for text color with real-time preview"""
        color = colorchooser.askcolor(title="Choose Text Color", initialcolor=self.config["text_color"])
        if color[1]:
            self.config["text_color"] = color[1]
            self.update_overlay_colors()
            self.save_config()
    
    def choose_bg_color(self):
        """Open color chooser for background color with real-time preview"""
        color = colorchooser.askcolor(title="Choose Background Color", initialcolor=self.config["bg_color"])
        if color[1]:
            self.config["bg_color"] = color[1]
            self.update_overlay_colors()
            self.save_config()
    
    def adjust_opacity(self):
        """Adjust overlay opacity with real-time preview"""
        opacity_window = tk.Toplevel(self.root)
        opacity_window.title("Adjust Opacity")
        opacity_window.geometry("500x500")
        opacity_window.resizable(False, False)
        
        ttk.Label(opacity_window, text="Opacity:").pack(pady=10)
        
        opacity_slider = ttk.Scale(opacity_window, from_=0.1, to=1.0, orient=tk.HORIZONTAL, 
                                  value=self.config["opacity"], command=self.update_opacity)
        opacity_slider.pack(pady=5, fill=tk.X, padx=20)
        
        # Opacity value display
        opacity_value_var = tk.StringVar(value=f"{int(self.config['opacity'] * 100)}%")
        opacity_label = ttk.Label(opacity_window, textvariable=opacity_value_var)
        opacity_label.pack(pady=5)
        
        # Update value display
        def update_value(value):
            opacity_value_var.set(f"{int(float(value) * 100)}%")
        
        opacity_slider.bind("<Motion>", lambda e: update_value(opacity_slider.get()))
        opacity_slider.bind("<ButtonRelease-1>", lambda e: update_value(opacity_slider.get()))
        
        ttk.Button(opacity_window, text="OK", command=opacity_window.destroy).pack(pady=5)
    
    def update_opacity(self, value):
        """Update overlay opacity in real-time"""
        self.config["opacity"] = float(value)
        self.overlay.attributes("-alpha", self.config["opacity"])
        self.save_config()
    
    def update_overlay_colors(self):
        """Update overlay colors"""
        self.overlay_label.configure(foreground=self.config["text_color"])
        # Set background color for the frame and label
        self.overlay_frame.configure(style="Overlay.TFrame")
        self.overlay_label.configure(style="Overlay.TLabel")
        
        # Create custom styles
        style = ttk.Style()
        style.configure("Overlay.TFrame", background=self.config["bg_color"])
        style.configure("Overlay.TLabel", background=self.config["bg_color"])
    

    
    def choose_font(self):
        """Open font selection window with real-time preview"""
        font_window = tk.Toplevel(self.root)
        font_window.title("Font Selection")
        font_window.geometry("450x350")
        font_window.resizable(False, False)
        
        # Font family selection
        ttk.Label(font_window, text="Font Family:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        font_family_var = tk.StringVar(value=self.config["font_family"])
        font_family_combobox = ttk.Combobox(font_window, textvariable=font_family_var, 
                                           values=sorted(tkfont.families()), state="readonly")
        font_family_combobox.grid(row=0, column=1, padx=10, pady=10, sticky=tk.EW)
        
        # Font size selection
        ttk.Label(font_window, text="Font Size:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        font_size_var = tk.IntVar(value=self.config["font_size"])
        font_size_spinbox = ttk.Spinbox(font_window, from_=10, to=200, textvariable=font_size_var)
        font_size_spinbox.grid(row=1, column=1, padx=10, pady=10, sticky=tk.EW)
        
        # Preview label
        ttk.Label(font_window, text="Preview:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        preview_var = tk.StringVar(value="12:34:56")
        preview_label = ttk.Label(font_window, textvariable=preview_var, 
                                font=(font_family_var.get(), font_size_var.get(), "bold"))
        preview_label.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
        
        # Update preview when font family changes
        def update_preview():
            preview_label.configure(font=(font_family_var.get(), font_size_var.get(), "bold"))
            # Apply real-time preview to overlay
            self.config["font_family"] = font_family_var.get()
            self.config["font_size"] = font_size_var.get()
            self.overlay_label.configure(font=(font_family_var.get(), font_size_var.get(), "bold"))
            if self.dynamic_size_var.get():
                self.adjust_overlay_size()
        
        font_family_combobox.bind("<<ComboboxSelected>>", lambda e: update_preview())
        font_size_spinbox.bind("<KeyRelease>", lambda e: update_preview())
        font_size_spinbox.bind("<ButtonRelease-1>", lambda e: update_preview())
        
        # Apply button
        ttk.Button(font_window, text="Apply", command=lambda: self.apply_font(font_family_var.get(), 
                                                                             font_size_var.get(), font_window)).grid(row=3, column=0, columnspan=2, 
                                                                                                                padx=10, pady=10, sticky=tk.EW)
        
        # Cancel button
        ttk.Button(font_window, text="Cancel", command=lambda: self.reset_font_preview(font_window)).grid(row=4, column=0, columnspan=2, 
                                                                                                      padx=10, pady=5, sticky=tk.EW)
        
        # Configure grid weights
        font_window.grid_columnconfigure(1, weight=1)
    
    def reset_font_preview(self, window):
        """Reset font settings if user cancels font selection"""
        self.overlay_label.configure(font=(self.config["font_family"], self.config["font_size"], "bold"))
        if self.dynamic_size_var.get():
            self.adjust_overlay_size()
        window.destroy()
    
    def apply_font(self, family, size, window):
        """Apply selected font settings to overlay"""
        self.config["font_family"] = family
        self.config["font_size"] = size
        
        # Update overlay font
        self.overlay_label.configure(font=(family, size, "bold"))
        
        # Adjust window size if dynamic sizing is enabled
        if self.dynamic_size_var.get():
            self.adjust_overlay_size()
        
        self.save_config()
        window.destroy()
    
    def toggle_dynamic_size(self):
        """Toggle dynamic size (auto-fit) behavior"""
        self.config["auto_size"] = self.dynamic_size_var.get()
        
        if self.dynamic_size_var.get():
            # Enable dynamic sizing
            self.adjust_overlay_size()
            self.overlay.resizable(False, False)
            # Remove resize bindings
            self.overlay.unbind("<ButtonPress-3>")
            self.overlay.unbind("<B3-Motion>")
        else:
            # Disable dynamic sizing - allow manual resizing
            self.overlay.resizable(True, True)
            # Add resize bindings
            self.overlay.bind("<ButtonPress-3>", self.start_resize)
            self.overlay.bind("<B3-Motion>", self.resize_window)
        
        self.save_config()
    
    def adjust_overlay_size(self):
        """Adjust overlay size based on current text content and font"""
        font_obj = tkfont.Font(family=self.config["font_family"], size=self.config["font_size"], weight="bold")
        current_text = self.overlay_time_var.get()
        
        # Get dimensions based on current text
        text_width = font_obj.measure(current_text)
        text_height = font_obj.metrics('linespace')
        
        # Add minimal padding
        padding = 5
        new_width = text_width + padding
        new_height = text_height + padding
        
        # Update overlay size
        x, y = self.overlay.winfo_x(), self.overlay.winfo_y()
        self.overlay.geometry(f"{new_width}x{new_height}+{x}+{y}")
    
    def toggle_overlay(self):
        """Show or hide the floating overlay"""
        if self.show_overlay_var.get():
            self.overlay.deiconify()
        else:
            self.overlay.withdraw()
    
    def on_closing(self):
        """Handle application closing"""
        if self.is_running:
            if not messagebox.askyesno("Confirm Close", "Timer is running. Closing will cancel the timer. Are you sure?"):
                return
        
        # Save current overlay position and size
        self.config["overlay_position"] = (self.overlay.winfo_x(), self.overlay.winfo_y())
        self.config["overlay_size"] = (self.overlay.winfo_width(), self.overlay.winfo_height())
        self.save_timer_settings()
        self.save_config()
        
        # Perform shutdown if timer was running
        self.is_running = False
        
        # Destroy all windows
        self.overlay.destroy()
        self.root.destroy()

def main():
    """Main entry point"""
    root = tk.Tk()
    app = ShutdownTimerApp(root)
    
    # Add keyboard shortcuts
    root.bind("<Control-Key-s>", lambda e: app.start_timer())
    root.bind("<Control-Key-p>", lambda e: app.pause_timer() if app.is_running else None)
    root.bind("<Control-Key-c>", lambda e: app.cancel_timer() if app.is_running else None)
    root.bind("<Escape>", lambda e: app.on_closing())
    
    # Make application look like native Windows app
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    # Set window icon (if available)
    if getattr(sys, 'frozen', False):
        # If running from .exe
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    
    icon_path = os.path.join(base_path, "assets", "icon.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except:
            pass
    
    root.mainloop()

if __name__ == "__main__":
    main()