import tkinter as tk
from gui import App

def main():
    root = tk.Tk()
    # Optional: Set icon
    # root.iconbitmap('icon.ico') 
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
