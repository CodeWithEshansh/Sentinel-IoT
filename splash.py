import customtkinter as ctk

class SplashScreen:
    def __init__(self, parent, on_complete):
        self.parent = parent
        self.on_complete = on_complete
        
        self.frame = ctk.CTkFrame(self.parent, fg_color="#050505")
        self.frame.pack(fill="both", expand=True)
        
        # Cyber-aesthetic Title
        self.title_label = ctk.CTkLabel(
            self.frame, 
            text="SENTINEL IoT", 
            font=ctk.CTkFont(family="Segoe UI", size=60, weight="bold"), 
            text_color="#00e5ff"
        )
        self.title_label.place(relx=0.5, rely=0.4, anchor="center")

        # Subtitle / Loading Text
        self.loading_label = ctk.CTkLabel(
            self.frame, 
            text="Initializing Secure Environment...", 
            font=ctk.CTkFont(family="Consolas", size=14), 
            text_color="#aaaaaa"
        )
        self.loading_label.place(relx=0.5, rely=0.6, anchor="center")

        # Progress bar
        self.progress = ctk.CTkProgressBar(
            self.frame, 
            width=400, 
            height=8, 
            progress_color="#00e5ff", 
            fg_color="#1a1a1a",
            border_width=0
        )
        self.progress.place(relx=0.5, rely=0.65, anchor="center")
        self.progress.set(0)

        # Sequence of loading states
        self.steps = [
            ("Initializing Secure Environment...", 0.25, 600),
            ("Loading AI Detection Engine...", 0.50, 700),
            ("Establishing Zero Trust Network...", 0.85, 700),
            ("System Ready", 1.0, 500)
        ]
        self.current_step = 0
        self.run_sequence()

    def run_sequence(self):
        if self.current_step < len(self.steps):
            text, progress_val, delay = self.steps[self.current_step]
            self.loading_label.configure(text=text)
            self.progress.set(progress_val)
            self.current_step += 1
            self.parent.after(delay, self.run_sequence)
        else:
            self.frame.destroy()
            self.on_complete()

def show_splash(parent, on_complete):
    SplashScreen(parent, on_complete)
