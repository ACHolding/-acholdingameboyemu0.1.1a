import tkinter as tk
from tkinter import filedialog, messagebox
import sys

try:
    from PIL import Image, ImageTk
except ImportError:
    print("Error: Pillow is not installed. Please run: pip install Pillow")
    sys.exit(1)

try:
    from pyboy import PyBoy
    from pyboy.utils import WindowEvent
except ImportError:
    print("Error: PyBoy is not installed. Please run: pip install pyboy")
    sys.exit(1)

class GBEmuApp:
    def __init__(self, root):
        self.root = root
        self.root.title(
            "ac and gemini's gameboy emulator 0.1 | "
            "[C] Nintendo 1985-2026 [C] AC HOLDINGS 1999-2026"
        )
        self.root.geometry("600x400")
        
        # Engine Blue Hue background
        self.engine_blue = "#001a33"
        self.root.configure(bg=self.engine_blue)

        # Styling Definitions
        self.btn_bg = "black"
        self.btn_fg = "blue"
        self.font_style = ("Consolas", 10, "bold")

        self.pyboy = None
        self.running = False
        
        self.setup_ui()
        self.setup_keybindings()

    def setup_ui(self):
        # Top Control Frame
        self.ctrl_frame = tk.Frame(self.root, bg=self.engine_blue)
        self.ctrl_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        # Buttons (Black background, Blue text)
        self.btn_load = tk.Button(
            self.ctrl_frame, 
            text="LOAD ROM", 
            bg=self.btn_bg, 
            fg=self.btn_fg, 
            font=self.font_style,
            activebackground=self.btn_fg,
            activeforeground=self.btn_bg,
            command=self.load_rom
        )
        self.btn_load.pack(side=tk.LEFT, padx=10)

        self.btn_stop = tk.Button(
            self.ctrl_frame, 
            text="STOP", 
            bg=self.btn_bg, 
            fg=self.btn_fg, 
            font=self.font_style,
            activebackground=self.btn_fg,
            activeforeground=self.btn_bg,
            command=self.stop_emulator,
            state=tk.DISABLED
        )
        self.btn_stop.pack(side=tk.LEFT, padx=10)

        # Core Info Label
        self.core_label = tk.Label(
            self.ctrl_frame, 
            text="Engine: PyBoy (mGBA fallback disabled)", 
            bg=self.engine_blue, 
            fg=self.btn_fg,
            font=("Consolas", 8)
        )
        self.core_label.pack(side=tk.RIGHT, padx=10)

        # Game Boy Screen (Center)
        self.screen_container = tk.Frame(self.root, bg="black", width=320, height=288)
        self.screen_container.pack(expand=True)
        self.screen_container.pack_propagate(False) # Force size

        self.screen_label = tk.Label(self.screen_container, bg="black", text="NO ROM LOADED", fg="blue")
        self.screen_label.pack(expand=True, fill=tk.BOTH)

        # Controls Info (Bottom)
        controls_text = "Controls: Arrows=D-Pad | Z=A | X=B | Enter=Start | Shift=Select"
        self.info_label = tk.Label(self.root, text=controls_text, bg=self.engine_blue, fg=self.btn_fg, font=("Consolas", 9))
        self.info_label.pack(side=tk.BOTTOM, pady=5)

    def setup_keybindings(self):
        # Map Tkinter Keys to PyBoy WindowEvents
        self.key_map = {
            'Up': (WindowEvent.PRESS_ARROW_UP, WindowEvent.RELEASE_ARROW_UP),
            'Down': (WindowEvent.PRESS_ARROW_DOWN, WindowEvent.RELEASE_ARROW_DOWN),
            'Left': (WindowEvent.PRESS_ARROW_LEFT, WindowEvent.RELEASE_ARROW_LEFT),
            'Right': (WindowEvent.PRESS_ARROW_RIGHT, WindowEvent.RELEASE_ARROW_RIGHT),
            'z': (WindowEvent.PRESS_BUTTON_A, WindowEvent.RELEASE_BUTTON_A),
            'Z': (WindowEvent.PRESS_BUTTON_A, WindowEvent.RELEASE_BUTTON_A),
            'x': (WindowEvent.PRESS_BUTTON_B, WindowEvent.RELEASE_BUTTON_B),
            'X': (WindowEvent.PRESS_BUTTON_B, WindowEvent.RELEASE_BUTTON_B),
            'Return': (WindowEvent.PRESS_BUTTON_START, WindowEvent.RELEASE_BUTTON_START),
            'Shift_R': (WindowEvent.PRESS_BUTTON_SELECT, WindowEvent.RELEASE_BUTTON_SELECT),
            'Shift_L': (WindowEvent.PRESS_BUTTON_SELECT, WindowEvent.RELEASE_BUTTON_SELECT),
        }

        # bind_all so keys work when focus is on buttons (not only the root window)
        self.root.bind_all("<KeyPress>", self.handle_keypress)
        self.root.bind_all("<KeyRelease>", self.handle_keyrelease)

    def load_rom(self):
        filepath = filedialog.askopenfilename(
            title="Select Game Boy ROM",
            filetypes=[("Gameboy ROMs", "*.gb *.gbc"), ("All Files", "*.*")]
        )
        if filepath:
            self.start_emulator(filepath)

    def start_emulator(self, rom_path):
        self.stop_emulator()
        
        try:
            # Initialize PyBoy in headless 'null' mode to extract frame buffers to Tkinter
            self.pyboy = PyBoy(rom_path, window="null")
            self.pyboy.set_emulation_speed(1) # Normal speed
            
            self.running = True
            self.btn_stop.config(state=tk.NORMAL)
            self.screen_label.config(text="")
            self.root.focus_set()

            # Start the game loop
            self.run_frame()
            
        except Exception as e:
            self.running = False
            messagebox.showerror("Emulator Error", f"Could not load ROM:\n{e}")
            self.pyboy = None
            self.btn_stop.config(state=tk.DISABLED)

    def stop_emulator(self):
        self.running = False
        if self.pyboy:
            self.pyboy.stop()
            self.pyboy = None
        self.screen_label.config(image=None, text="NO ROM LOADED")
        self.btn_stop.config(state=tk.DISABLED)

    def handle_keypress(self, event):
        if not self.pyboy: return
        keys = self.key_map.get(event.keysym)
        if keys:
            self.pyboy.send_input(keys[0])

    def handle_keyrelease(self, event):
        if not self.pyboy: return
        keys = self.key_map.get(event.keysym)
        if keys:
            self.pyboy.send_input(keys[1])

    def run_frame(self):
        if self.running and self.pyboy:
            # Advance emulator by one frame; False means emulation ended
            if not self.pyboy.tick():
                self.stop_emulator()
                return

            # Grab the screen buffer and convert it to a Pillow Image
            try:
                # Copy: screen.image is backed by a live buffer that tick() mutates
                image = self.pyboy.screen.image.copy()

                # Original GB resolution is 160x144. We upscale it 2x to 320x288 using nearest neighbor
                image = image.resize((320, 288), Image.NEAREST)
                
                # Convert to Tkinter PhotoImage and display
                self.photo = ImageTk.PhotoImage(image)
                self.screen_label.config(image=self.photo)
                
            except Exception as e:
                print(f"Render error: {e}")
            
            # GameBoy runs at ~60 FPS (approx 16.7 ms per frame)
            self.root.after(16, self.run_frame)

if __name__ == "__main__":
    root = tk.Tk()
    app = GBEmuApp(root)
    
    # Handle window closing gracefully
    def on_closing():
        app.stop_emulator()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()