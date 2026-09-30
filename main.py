import flet as ft
import sqlite3
import os
from pathlib import Path
from datetime import datetime
import urllib.parse

def main(page: ft.Page):
    # ==========================================
    # 1. CONFIGURACIÓN DE LA PÁGINA
    # ==========================================
    page.window.width = 380
    page.window.height = 680
    page.title = "Mi Balance"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#263238"  # HEX real para evitar fallos de renderizado
    page.padding = 20

    # ==========================================
    # 2. BASE DE DATOS BLINDADA (MÓVIL)
    # ==========================================
    try:
        if page.platform == ft.PagePlatform.ANDROID or page.platform == ft.PagePlatform.IOS:
            directorio_base = Path(page.get_user_data_dir())
        else:
            directorio_base = Path(os.getcwd())
            
        directorio_base.mkdir(parents=True, exist_ok=True)
        DB_NAME = str(directorio_base / "finanzas_personales.db")
    except:
        DB_NAME = "finanzas_respaldo.db"

    def inicializar_bd():
        try:
            conexion = sqlite3.connect(DB_NAME)
            cursor = conexion.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS perfil (
                                id INTEGER PRIMARY KEY, 
                                nombre TEXT, 
                                telefono TEXT, 
                                correo TEXT)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS movimientos (
                                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                fecha TEXT, 
                                concepto TEXT, 
                                monto REAL)''')
            conexion.commit()
            conexion.close()
        except Exception as e:
            print(f"Error BD: {e}")

    inicializar_bd()

    def notificar(mensaje, color="#388E3C"):
        snack = ft.SnackBar(ft.Text(mensaje, color="#FFFFFF"), bgcolor=color, duration=3000)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # ==========================================
    # 3. PANTALLA DE REGISTRO (PRIMERA VEZ)
    # ==========================================
    def mostrar_registro():
        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        txt_nombre = ft.TextField(label="Nombre y Apellido", prefix_icon="person", width=300)
        txt_telefono = ft.TextField(label="Nro de Teléfono (Ej: +584242153625)", keyboard_type=ft.KeyboardType.PHONE, prefix_icon="phone", width=300)
        txt_correo = ft.TextField(label="Correo Electrónico", keyboard_type=ft.KeyboardType.EMAIL, prefix_icon="email", width=300)

        def guardar_perfil(e):
            if txt_nombre.value and txt_telefono.value and txt_correo.value:
                try:
                    conexion = sqlite3.connect(DB_NAME)
                    cursor = conexion.cursor()
                    cursor.execute("INSERT INTO perfil (nombre, telefono, correo) VALUES (?, ?, ?)", 
                                   (txt_nombre.value.strip(), txt_telefono.value.strip(), txt_correo.value.strip()))
                    conexion.commit()
                    conexion.close()
                    notificar("Perfil creado con éxito")
                    mostrar_principal()
                except Exception as ex:
                    notificar(f"Error al guardar: {ex}", "#D32F2F")
            else:
                notificar("Por favor completa todos los campos", "#F57C00")

        page.add(
            ft.Icon("account_circle", size=80, color="#42A5F5"),
            ft.Text("Bienvenido", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("Configura tu perfil para los reportes", size=14, color="#8AFFFFFF"),
            ft.Divider(height=20, color="#00000000"),
            txt_nombre,
            txt_telefono,
            txt_correo,
            ft.Divider(height=10, color="#00000000"),
            ft.FilledButton("Guardar y Comenzar", on_click=guardar_perfil, width=300, style=ft.ButtonStyle(bgcolor="#1E88E5"))
        )

    # ==========================================
    # 4. PANTALLA PRINCIPAL (BALANCE)
    # ==========================================
    def mostrar_principal():
        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        # Lectura segura del perfil
        try:
            conexion = sqlite3.connect(DB_NAME)
            cursor = conexion.cursor()
            cursor.execute("SELECT nombre, telefono, correo FROM perfil LIMIT 1")
            perfil = cursor.fetchone()
            conexion.close()
            nombre_usuario, telefono_usuario, correo_usuario = perfil if perfil else ("Usuario", "", "")
        except:
            nombre_usuario, telefono_usuario, correo_usuario = ("Usuario", "", "")

        texto_balance = ft.Text("$0.00", size=45, weight=ft.FontWeight.BOLD, color="#FFFFFF")
        contenedor_balance = ft.Container(
            content=ft.Column([
                ft.Text(f"CAPITAL DE {nombre_usuario.upper()}", size=12, color="#B3FFFFFF", weight=ft.FontWeight.BOLD),
                texto_balance
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment.CENTER,
            padding=10
        )

        lista_historial = ft.ListView(expand=True, spacing=5)
        
        selector_fecha = ft.DatePicker(on_change=lambda e: actualizar_texto_fecha())
        page.overlay.append(selector_fecha)
        texto_fecha = ft.Text(datetime.now().strftime("%d/%m/%Y"))
        
        def actualizar_texto_fecha():
            if selector_fecha.value:
                texto_fecha.value = selector_fecha.value.strftime("%d/%m/%Y")
                page.update()

        def abrir_calendario(e):
            selector_fecha.open = True
            page.update()

        boton_fecha = ft.OutlinedButton(content=texto_fecha, icon="calendar_month", on_click=abrir_calendario)

        entrada_concepto = ft.TextField(label="Concepto", expand=True)
        entrada_monto = ft.TextField(label="Monto ($)", keyboard_type=ft.KeyboardType.NUMBER, width=110)

        def cargar_datos():
            lista_historial.controls.clear()
            try:
                conexion = sqlite3.connect(DB_NAME)
                cursor = conexion.cursor()
                cursor.execute("SELECT fecha, concepto, monto FROM movimientos ORDER BY id DESC")
                movimientos = cursor.fetchall()
                conexion.close()
                
                total = 0.0
                for mov in movimientos:
                    fecha, concepto, monto = mov
                    total += monto
                    
                    es_ingreso = monto >= 0
                    icono = "arrow_upward" if es_ingreso else "arrow_downward"
                    color_icono = "#66BB6A" if es_ingreso else "#EF5350"
                    signo = "+" if es_ingreso else ""
                    
                    tarjeta = ft.Card(
                        color="#37474F", 
                        content=ft.ListTile(
                            leading=ft.Icon(icono, color=color_icono),
                            title=ft.Text(concepto, weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(fecha, color="#8AFFFFFF", size=12),
                            trailing=ft.Text(f"{signo}${monto:.2f}", color=color_icono, weight=ft.FontWeight.BOLD, size=16)
                        )
                    )
                    lista_historial.controls.append(tarjeta)

                texto_balance.value = f"${total:.2f}"
                texto_balance.color = "#EF5350" if total < 0 else "#66BB6A"
                page.update()
            except Exception as e:
                notificar(f"Error cargando historial: {e}", "#D32F2F")

        def agregar_movimiento(e, tipo):
            if not entrada_monto.value or not entrada_concepto.value:
                return notificar("Llene ambos campos", "#F57C00")
                
            try:
                monto = float(entrada_monto.value.replace(",", "."))
                if tipo == "gasto":
                    monto = -monto
                
                conexion = sqlite3.connect(DB_NAME)
                cursor = conexion.cursor()
                cursor.execute("INSERT INTO movimientos (fecha, concepto, monto) VALUES (?, ?, ?)", 
                               (texto_fecha.value, entrada_concepto.value, monto))
                conexion.commit()
                conexion.close()
                
                entrada_monto.value = ""
                entrada_concepto.value = ""
                cargar_datos()
            except ValueError:
                notificar("Monto numérico inválido", "#D32F2F")
            except Exception as e:
                notificar(f"Error al guardar: {e}", "#D32F2F")

        # Menú desplegable para compartir reporte
        opcion_envio_reporte = ft.Dropdown(
            label="Enviar Reporte por:", 
            options=[ft.dropdown.Option("WhatsApp"), ft.dropdown.Option("Correo Electrónico")], 
            value="WhatsApp", 
            border_color="#42A5F5"
        )

        def procesar_envio_reporte(e):
            dialogo_reporte.open = False
            page.update()
            
            try:
                conexion = sqlite3.connect(DB_NAME)
                cursor = conexion.cursor()
                cursor.execute("SELECT nombre, telefono, correo FROM perfil LIMIT 1")
                perfil_actual = cursor.fetchone()
                
                cursor.execute("SELECT fecha, concepto, monto FROM movimientos ORDER BY id ASC")
                movs = cursor.fetchall()
                conexion.close()
                
                nom, tlf, corr = perfil_actual if perfil_actual else (nombre_usuario, telefono_usuario, correo_usuario)
                
                if not movs:
                    return notificar("No hay movimientos para compartir", "#F57C00")
                    
                total = sum(m[2] for m in movs)
                
                texto = f"📊 *ESTADO DE CUENTA*\n👤 Propietario: {nom}\n💰 Capital Actual: *${total:.2f}*\n\n*Detalle de Movimientos:*\n"
                for m in movs:
                    signo = "+" if m[2] >= 0 else ""
                    texto += f"• {m[0]} | {m[1]}: {signo}${m[2]:.2f}\n"
                    
                texto_codificado = urllib.parse.quote(texto)
                
                if opcion_envio_reporte.value == "WhatsApp":
                    if not tlf:
                        return notificar("No hay número de teléfono registrado", "#F57C00")
                    tel_limpio = tlf.replace('+', '').replace(' ', '')
                    page.launch_url(f"whatsapp://send?phone={tel_limpio}&text={texto_codificado}")
                    
                elif opcion_envio_reporte.value == "Correo Electrónico":
                    if not corr:
                        return notificar("No hay correo registrado", "#F57C00")
                    asunto_codificado = urllib.parse.quote(f"Mi Balance - {nom}")
                    enlace_correo = f"https://mail.google.com/mail/?view=cm&fs=1&to={corr}&su={asunto_codificado}&body={texto_codificado}"
                    page.launch_url(enlace_correo)
                    
            except Exception:
                notificar("Error al procesar reporte", "#D32F2F")

        dialogo_reporte = ft.AlertDialog(
            title=ft.Text("Compartir Balance", weight=ft.FontWeight.BOLD), 
            content=ft.Column([
                ft.Text("Selecciona el medio para enviar tu estado de cuenta detallado."), 
                opcion_envio_reporte
            ], tight=True), 
            actions=[
                ft.FilledButton("Compartir", on_click=procesar_envio_reporte, style=ft.ButtonStyle(bgcolor="#1E88E5", color="#FFFFFF")), 
                ft.TextButton("Cancelar", on_click=lambda e: cerrar_dialogo())
            ], 
            actions_alignment=ft.MainAxisAlignment.CENTER
        )
        
        page.overlay.append(dialogo_reporte)

        def abrir_dialogo_reporte(e):
            dialogo_reporte.open = True
            page.update()

        def cerrar_dialogo():
            dialogo_reporte.open = False
            page.update()

        page.add(
            contenedor_balance,
            ft.Row([boton_fecha], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([entrada_concepto, entrada_monto]),
            ft.Row([
                ft.FilledButton("Ingreso", icon="add", style=ft.ButtonStyle(bgcolor="#43A047"), on_click=lambda e: agregar_movimiento(e, "ingreso"), expand=True),
                ft.FilledButton("Gasto", icon="remove", style=ft.ButtonStyle(bgcolor="#E53935"), on_click=lambda e: agregar_movimiento(e, "gasto"), expand=True)
            ]),
            ft.Divider(height=15, color="#00000000"),
            ft.Text("HISTORIAL DE MOVIMIENTOS", weight=ft.FontWeight.BOLD, color="#8AFFFFFF", size=12),
            lista_historial, 
            ft.ElevatedButton(
                "Compartir Reporte", 
                icon="share", 
                bgcolor="#1E88E5", 
                color="#FFFFFF",
                on_click=abrir_dialogo_reporte,
                width=float('inf') 
            )
        )
        cargar_datos()

    # ==========================================
    # 5. CONTROL DE ACCESO INICIAL BLINDADO
    # ==========================================
    try:
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()
        cursor.execute("SELECT id FROM perfil LIMIT 1")
        usuario_existente = cursor.fetchone()
        conexion.close()

        if usuario_existente:
            mostrar_principal()
        else:
            mostrar_registro()
    except Exception as e:
        mostrar_registro()

ft.app(target=main)
