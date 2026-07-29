import ttkbootstrap as ttk


class LoadModal(ttk.Toplevel):
    def __init__(self, parent, message="Generando Archivos..."):
        super().__init__(parent)
        ventana_principal = parent.winfo_toplevel()

        # Obtener dimensiones y coordenadas de la ventana principal
        padre_ancho = ventana_principal.winfo_width()
        padre_alto = ventana_principal.winfo_height()
        padre_x = ventana_principal.winfo_rootx()
        padre_y = ventana_principal.winfo_rooty()

        # Calcular coordenadas de centrado (ejemplo con modal de 300x120)
        pos_x = padre_x + (padre_ancho // 2) - (300 // 2)
        pos_y = padre_y + (padre_alto // 2) - (120 // 2)

        self.geometry(f"300x120+{pos_x}+{pos_y}") # Centra la ventana modal sobre la ventana principal
        self.title("Trabajando")
        self.resizable(False, False)
        self.transient(parent) #centra la ventana modal sobre la ventana principal
        self.grab_set() #bloquea la ventana principal mientras el modal está abierto

        label = ttk.Label(self, text=message, font=("Helvetica", 12))
        label.pack(pady=20)

        progress_bar = ttk.Progressbar(self, mode="indeterminate")
        progress_bar.pack(fill="none", padx=20, pady=10)
        progress_bar.start(10)  # Ajusta la velocidad de la animación si es necesario
        