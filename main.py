import tkinter as tk
from PIL import Image, ImageTk # <-- Import from Pillow
from ui.main_app_window import ScoutManagerApp

if __name__ == "__main__":
    root = tk.Tk()
    root.state('zoomed')

    pil_image = Image.open("icons/app_icon.png")
    icon_image = ImageTk.PhotoImage(pil_image)
    root.iconphoto(True, icon_image)

    app = ScoutManagerApp(root)
    root.mainloop()