import asyncio
import datetime
import os
import time
import shutil
import openpyxl
import re
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from getDatos import read_codes_text, write_online_codes_text
from updateCodeSIM import update_codes_text, read_last_update_time, do_update
import ctypes
from load_modal import LoadModal


ruta_alta = "PMC_Creados/"
ruta_codigos = "utils/codigosSIM.txt"

#llamamos a la funcion de conexion a la Api de Google Drive
try:
    online_data = read_codes_text()
    """Capturamos la ultima fecha de actualización del archivo de códigos desde Drive o local para mostrar en la interfaz y para comparar si es necesario actualizar el archivo local. Si no se puede conectar a Drive, se asume que el archivo local es el más reciente."""""
    if online_data["payload"] != "":
        payload_time_refresh = online_data["payload"].splitlines()[2].strip()
        print(f"Modo de lectura: {online_data['mode']} - Status: {online_data['status']}")
    else:
        payload_time_refresh = "1970-01-01 00:00:00"
except Exception as e:
    online_data = {"payload": "", "mode": "local", "status": f"Error al conectar con Drive: {e}"}
    payload_time_refresh = "1970-01-01 00:00:00"
    print(f"Modo de lectura: {online_data['mode']} - Status: {online_data['status']}")

    


# 1. Configurar el ID para la barra de tareas antes de crear la ventana
try:
    myappid = 'appAltaScada.1.1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass # Evita errores si se ejecuta en Mac o Linux

class App(ttk.Window):
    def __init__(self, root):
        self.root = root
        self.init_ui()
        self.createWidget()

    def init_ui(self):
        self.root.resizable(False, False)
        self.root.iconbitmap("docs/logoOSE.ico")
        self.root.title("Alta Punto SCADA")
        self.root.geometry("600x680")

    def createWidget(self):
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        #titulo
        title_label = ttk.Label(main_frame, text="Alta Punto SCADA", font=("Arial", 20))
        title_label.pack(pady=20)
        
        #infomarcion de Tabla de Variables
        ttk.Label(main_frame, text="Tablas de Variables conforme version 1.0.7 del Programa control SGD-RTUX", font=("Arial", 8), bootstyle="secondary").pack(pady=(0,10))
        if online_data["mode"] == "local":
            ttk.Label(main_frame, text="Error al conectar con Google Drive. Usando archivo local.", font=("Arial", 8), bootstyle="danger").pack(pady=(0,10))
        else:
            ttk.Label(main_frame, text="--App Sincronizada--", font=("Arial", 8), bootstyle="success").pack(pady=(0,10)) 
    
        #ttk.label(main_frame, text=f"Ultima Actualizacion: {time.strftime('%Y-%m-%d %H:%M:%S')}" )
        #frame para los inputs
        input_frame = ttk.Labelframe(main_frame, text="Datos del PMC", padding=15)
        input_frame.pack(pady=(0,20), fill=X)
        
        #Input para el nombre del PMC
        name_label = ttk.Label(input_frame, text="Nombre del PMC")  
        name_label.pack(pady=(0,10))
        self.pmc_name_var = ttk.StringVar()
        self.pmc_name_entry = ttk.Entry(input_frame, textvariable=self.pmc_name_var)
        self.pmc_name_entry.focus()
        self.pmc_name_entry.pack(pady=(0,10))
        
        #Input para el Codigo del PMC
        code_label = ttk.Label(input_frame, text="Codigo del PMC")
        code_label.pack(pady=(0,10))
        self.pmc_code_var = ttk.StringVar()
        self.pmc_code_entry = ttk.Entry(input_frame, textvariable=self.pmc_code_var)
        self.pmc_code_entry.pack(pady=(0,10))
        
        #Radio buttons para seleccionar el tipo de Hardware
        hardware_label = ttk.Label(input_frame, text="Tipo de Hardware")
        hardware_label.pack(pady=(0,20))
        self.hardware_var = ttk.StringVar()
        hardware_options = ["RTU+","RTUX"]
        for option in hardware_options:
            if option == "RTU+":
                ttk.Label(input_frame, text="-> Migracion Finalizada <-", font=("Arial", 9), bootstyle="secondary").pack(pady=(0,1))
                ttk.Label(input_frame, text="Equipos en Deshuso", font=("Arial", 8), bootstyle="secondary").pack(pady=(0,1))
                ttk.Radiobutton(input_frame, text=option, variable=self.hardware_var, value=option).pack(pady=(0,10))
            else:
                ttk.Radiobutton(input_frame, text=option, variable=self.hardware_var, value=option).pack(pady=(0,10))
            
        self.hardware_var.set(hardware_options[1])  # Selección por defecto 
        
        # SOLUCIÓN: Llamar correctamente la función asíncrona
        create_button = ttk.Button(
            main_frame, 
            text="Crear PMC File", 
            bootstyle="success",
            command=self.handle_create_pmc  # ← Cambio aquí
        )
        create_button.pack(pady=30, fill=X)
        #footer con separador y texto de desarrollador
        ttk.Separator(main_frame, bootstyle="secondary").pack(pady=5, fill=X)
        ttk.Label(main_frame, text="Desarrollado por: Marcelo Rodriguez SGD - 2026", font=("Arial", 10), bootstyle="secondary").pack(pady=10)
        ttk.Label(main_frame, text="Ver 1.2", font=("Arial", 9), bootstyle="secondary").pack(pady=(0,10))
       

          
    def handle_create_pmc(self):
        """
        Wrapper síncrono para llamar a la función asíncrona
        """
        asyncio.run(self.createPMCFile())  # ← Ahora sí con ()

    def validateInputs(self):
        """Valida que los inputs no esten vacios"""
        if not self.pmc_name_var.get():
            Messagebox.show_error("El nombre del PMC no puede estar vacio","Error")
            return False
        if not self.pmc_code_var.get():
            Messagebox.show_error("El codigo del PMC no puede estar vacio","Error")
            return False
        if not self.hardware_var.get():
            Messagebox.show_error("Debe seleccionar un tipo de hardware","Error")
            return False
        return True

    async def createPMCFile(self,load_modal=None):

        """Crea el archivo PMC con los datos ingresados"""
        if not self.validateInputs():
            return
        
        pmc_name = self.pmc_name_var.get().capitalize()
        pmc_code = self.pmc_code_var.get().capitalize()
        hardware_type = self.hardware_var.get()

        answer = Messagebox.yesno(
            f"PMC File - Confirmar datos\nNombre: {pmc_name}\nCodigo: {pmc_code}\nHardware: {hardware_type}", 
            "PMC File"
        )

        if answer != "Yes":
            Messagebox.show_info("Cancelacion creacion de archivos PMC","PMC File")
            return
        else:
            # Mostrar modal de carga
            if load_modal is None:
                load_modal = LoadModal(self.root, message="Generando Archivos...",)
            load_modal.update()  # Asegura que el modal se muestre antes de continuar
            await asyncio.sleep(0.1)  # Permite que el modal se renderice correctamente
            
            

            
        #empieza Modal de carga
        
        # Crear carpeta
        createPMCFolder(pmc_name)
        load_modal.update()  # Actualiza el modal después de crear la carpeta
        # Buscar códigos
        codigosPMC = searchPMCCode(ruta_codigos)
        
        if not codigosPMC:
            load_modal.destroy()
            return
        
        try:
            load_modal.update()  # Actualiza el modal antes de iniciar la creación de archivos
            # Ejecutar funciones asíncronas
            await createTGDFile(pmc_code)
            await createCSVFile(hardware_type, pmc_name, pmc_code, codigosPMC)
            
            #cierro el modal de carga
            load_modal.destroy()
            Messagebox.ok("Archivo PMC creado con éxito", "PMC File")
            
            # Limpiar inputs
            self.pmc_code_var.set("")
            self.pmc_name_var.set("")
            self.hardware_var.set("")
        except Exception as e:
            Messagebox.show_error(f"Error al crear los archivos: {e}", "Error")



def createPMCFolder(name_folder:str) -> None:
    """Creacion de Carpeta PMC"""
    folder_path = os.path.join(ruta_alta, name_folder)
    try:
        os.makedirs(folder_path, exist_ok=True)  # exist_ok=True evita error si ya existe
        print(f"Carpeta {name_folder} creada con éxito")
    except Exception as e:
        Messagebox.show_error(f"Error al crear carpeta: {e}", "Error")


def refreshLogFile(data:str) -> bool:
    """Actualiza el log de altas PMC"""
    try:
        with open("utils/log.txt", "a") as f:
            f.write(data + "\n")
        print("Log actualizado")
        return True
    except Exception as e:
        Messagebox.show_error(f"Error al escribir en el log: {e}", "Error")
        return False


def searchPMCCode(ruta:str) -> list:
    #CONTROL DE FECHA DE ACTUALIZACION DEL ARCHIVO DE CODIGOS, SI LA FECHA DE DRIVE ES MAS RECIENTE QUE LA LOCAL, SE ACTUALIZA EL ARCHIVO LOCAL
    last_local_update = read_last_update_time(ruta_codigos)
    
    if do_update(last_local_update,payload_time_refresh) and online_data["mode"] == "drive":
        list_codigo_online = []
        print("Actualizando archivo de codigos desde Google Drive")
        print(f"Buscando codigos en Google Drive: {online_data['payload']}")
        # Procesar el contenido de Google Drive
        for line in online_data['payload'].split('\n'):
            list_codigo_online.append(line.strip())
            print(f"Codigos PMC encontrados en drive: {list_codigo_online}")
        
        update_codes_text(list_codigo_online,ruta_codigos)
        return list_codigo_online

    else:
        """Busca el codigo PMC en el archivo .txt"""
        print(f"Buscando códigos PMC en: {ruta}")
        try:
            list_codigo = []
            with open(ruta, "r") as f:
                for line in f:
                    list_codigo.append(line.strip())
                print(f"Codigos PMC encontrados locales: {list_codigo}")
                write_online_codes_text(list_codigo)
                return list_codigo
        except FileNotFoundError:
                Messagebox.show_error("Archivo codigosSIM.txt no encontrado", "Error")
                return None
        

    


async def createCSVFile(hardware_name:str, pmc_name:str, pmc_code:str, last_codigo_pmc:list)-> None:
    """Crea el archivo CSV del PMC"""
    """Códigos de referencia para alarmas PC"""
        
    ref_codigo_pmc = 1980
    ref_codigo_doble_pmc = 1982
    ref_codigo_alarma = 178
    
    codigo_alarma_PMC_PC = '"' + str(ref_codigo_pmc) + '"'
    codigo_alarma_PMC = '"' + str(ref_codigo_doble_pmc) + '"'
    codigo_alarma = '"' + str(ref_codigo_alarma) + ':'
    print(f"Código de alarma PMC: {codigo_alarma_PMC}")
    print(f"Código de alarma PMC PC: {codigo_alarma_PMC_PC}")
 
    
    print(last_codigo_pmc)
    csv_filename = f"{pmc_code}.csv"
    
    try:
        # Copiar archivo de referencia
        shutil.copyfile(f"utils/{hardware_name}.csv", csv_filename)
        
        # Leer contenido
        with open(csv_filename, "r", encoding="utf-8") as f:
            contenido = f.read()
        
        # Hacer reemplazos
        contenido = contenido.replace(hardware_name, pmc_name)
        contenido = contenido.replace(pmc_name, pmc_code)  # Segunda pasada
        contenido = contenido.replace(hardware_name + "-", pmc_code + " -")
        contenido = contenido.replace(pmc_code + " ", pmc_name +" ") # Tercera pasada para asegurar reemplazo completo
        # Actualizar códigos
        nuevo_codigo_alarmas_PMC =  str(last_codigo_pmc[0])
        nuevo_codigo_alarmas_PMC_PC =  str(int(last_codigo_pmc[0])+2)
        nuevo_codigo_alarmas = str(int(last_codigo_pmc[1])+1)
        
        print(f"Nuevo código de alarma PMC: {nuevo_codigo_alarmas_PMC}")
        print(f"Nuevo código de alarma PMC PC: {nuevo_codigo_alarmas_PMC_PC}")
        print(f"Nuevo código PMC: {nuevo_codigo_alarmas}")
        
        # Reemplazos de códigos de alarma PC
        for i in range(2):
            contenido = contenido.replace(f'"{str(int(ref_codigo_pmc)+i)}"', f'"{(str(int(nuevo_codigo_alarmas_PMC)+i))}"')
            
        contenido = contenido.replace(str(codigo_alarma_PMC), f'"{(str(int(nuevo_codigo_alarmas_PMC_PC)))}"')
        
        print(f"Reemplazando código de alarma PMC: {codigo_alarma} por {nuevo_codigo_alarmas}") 
        contenido = contenido.replace(codigo_alarma, f'"{(str(nuevo_codigo_alarmas))}:')
        
        
        # Escribir contenido modificado
        with open(csv_filename, "w", encoding="utf-8") as f:
            f.write(contenido)
        
        #lista de codigos PMC actualizada
        updated_pmc_codes = [str(int(last_codigo_pmc[0]) + 3), str(int(last_codigo_pmc[1]) + 1), time.strftime('%Y-%m-%d %H:%M:%S')]
        #TODO: Implementar lógica de control y actualización de códigos en lo local como online del archivo de codigosSIM.txt
        #Llamar funciones de updateDatos para comparacion de fechas y actualizacion del archivo de codigos
     
        print(online_data['mode'])
        if online_data['mode'] == 'drive':
            print("Actualizando archivo de codigos Creados en Google Drive y en local")
            write_online_codes_text(updated_pmc_codes)
            # Actualizar tambien códigos en archivo de texto
            with open("utils/codigosSIM.txt", "w") as f:
                for line in updated_pmc_codes:
                    f.write(line + "\n")
        else:
            # Actualizar códigos en archivo de texto solamente
            print(f"Actualizando archivo de codigos local: utils/codigosSIM.txt")
            with open("utils/codigosSIM.txt", "w") as f:
                for line in updated_pmc_codes:
                    f.write(line + "\n")
        
        # AL FINALIZAR LA CREACION DEL CSV, SE MUEVEN LOS ARCHIVOS A LA CARPETA CORRESPONDIENTE
        # Mover archivos
        moveFiles(pmc_code, pmc_name)
        
        # Log de éxito
        refreshLogFile(
            f"PMC: {pmc_name} - Codigo: {pmc_code} - Hardware: {hardware_name} - "
            f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')} - CREADO con Exito"
        )
        print(f"✓ Archivo CSV creado: {csv_filename}")
        


        
    except FileNotFoundError:
        Messagebox.show_error(f"Archivo de referencia no encontrado: utils/{hardware_name}.csv", "Error")
        return
    except Exception as e:
        Messagebox.show_error(f"Error al crear CSV: {e}", "Error")
        refreshLogFile(
            f"PMC: {pmc_name} - Codigo: {pmc_code} - Hardware: {hardware_name} - "
            f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ERROR al dar de Alta el PMC"
        )
        return


async def createTGDFile(pmc_code):
    """Crea el archivo TGD del PMC"""
    tgd_filename = f"OSEDIS_{pmc_code}.xlsx"
    
    try:
        # Copiar archivo de referencia
        shutil.copyfile("utils/TagGrupo.xlsx", tgd_filename)
        
        # Leer contenido xlsx
        tagGroup = openpyxl.load_workbook(tgd_filename)
        sheet = tagGroup.active
        
        # Reemplazar RTU por el código PMC
        for row in range(1, sheet.max_row+1):
            cell = sheet.cell(row=row, column=2)
            if isinstance(cell.value, str):
                #DEBUG: print(f"Revisando celda B{row}: {cell.value}")
                cell.value = re.sub("RTU", pmc_code,cell.value,flags=re.IGNORECASE)

                
        openpyxl.writer.excel.save_workbook(tagGroup, tgd_filename)    

        
        print(f"✓ Archivo Xlsx creado: {tgd_filename}")
        # Cambio de Extensión a .tgd
        #os.rename(tgd_filename, f"OSEDIS_{pmc_code}.TGD")
        #print(f"✓ Archivo TGD renombrado: OSEDIS_{pmc_code}.TGD")
        
    except FileNotFoundError:
        Messagebox.show_error("Archivo TagGrupo.xlsx no encontrado", "Error")
        return
    except Exception as e:
        Messagebox.show_error(f"Error al crear TGD: {e}", "Error")
        return


def moveFiles(pmc_code, pmc_name):
    """Mueve los archivos creados a la carpeta del PMC"""
    try:
        destination_folder = os.path.join(ruta_alta, pmc_name)
        os.makedirs(destination_folder, exist_ok=True)
        
        csv_source = f"{pmc_code}.csv"
        tgd_source = f"OSEDIS_{pmc_code}.xlsx"
        
        csv_dest = os.path.join(destination_folder, f"{pmc_code}.csv")
        tgd_dest = os.path.join(destination_folder, f"OSEDIS_{pmc_code}.xlsx")
        
        if os.path.exists(csv_source):
            shutil.move(csv_source, csv_dest)
            print(f"✓ {csv_source} movido a {destination_folder}")
        
        if os.path.exists(tgd_source):
            shutil.move(tgd_source, tgd_dest)
            print(f"✓ {tgd_source} movido a {destination_folder}")
        
    except Exception as e:
        Messagebox.show_error(f"Error al mover archivos: {e}", "Error")


if __name__ == "__main__":
    root = ttk.Window(themename="superhero")
    app = App(root)
    root.mainloop()