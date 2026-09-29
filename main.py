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
    page.bgcolor = "blueGrey900" 
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

    def notificar(mensaje, color="green700"):
        snack = ft.SnackBar(ft.Text(mensaje, color="white"), bgcolor=color, duration=3000)
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
                    mostrar_principal((txt_nombre.value, txt_telefono.value, txt_correo.value))
                except Exception as ex:
                    notificar(f"Error al guardar: {ex}", "red700")
            else:
                notificar("Por favor completa todos los campos", "orange700")

        page.add(
            ft.Icon("account_circle", size=80, color="blue400"),
            ft.Text("Bienvenido", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("Configura tu perfil para los reportes", size=14, color="grey400"),
            ft.Divider(height=20, color="transparent"),
            txt_nombre,
            txt_telefono,
            txt_correo,
            ft.Divider(height=10, color="transparent"),
            ft.FilledButton("Guardar y Comenzar", on_click=guardar_perfil, width=300, style=ft.ButtonStyle(bgcolor="blue600"))
        )

    # ==========================================
    # 4. PANTALLA PRINCIPAL (BALANCE)
    # ==========================================
    def mostrar_principal(datos_usuario):
        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        nombre_usuario, telefono_usuario, correo_usuario = datos_usuario

        texto_balance = ft.Text("$0.00", size=45, weight=ft.FontWeight.BOLD, color="white")
        contenedor_balance = ft.Container(
            content=ft.Column([
                ft.Text(f"CAPITAL DE {nombre_usuario.upper()}", size=12, color="grey400", weight=ft.FontWeight.BOLD),
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
                    color_icono = "green400" if es_ingreso else "red400"
                    signo = "+" if es_ingreso else ""
                    
                    tarjeta = ft.Card(
                        color="blueGrey800", 
                        content=ft.ListTile(
                            leading=ft.Icon(icono, color=color_icono),
                            title=ft.Text(concepto, weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(fecha, color="grey400", size=12),
                            trailing=ft.Text(f"{signo}${monto:.2f}", color=color_icono, weight=ft.FontWeight.BOLD, size=16)
                        )
                    )
                    lista_historial.controls.append(tarjeta)

                texto_balance.value = f"${total:.2f}"
                texto_balance.color = "red400" if total < 0 else "green400"
                page.update()
            except Exception as e:
                notificar(f"Error cargando historial: {e}", "red700")

        def agregar_movimiento(e, tipo):
            if not entrada_monto.value or not entrada_concepto.value:
                return notificar("Llene ambos campos", "orange700")
                
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
                notificar("Monto numérico inválido", "red700")
            except Exception as e:
                notificar(f"Error al guardar: {e}", "red700")

        def enviar_reporte(e):
            try:
                conexion = sqlite3.connect(DB_NAME)
                cursor = conexion.cursor()
                cursor.execute("SELECT fecha, concepto, monto FROM movimientos ORDER BY id ASC")
                movs = cursor.fetchall()
                conexion.close()
                
                if not movs:
                    return notificar("No hay movimientos para compartir", "orange700")
                    
                total = sum(m[2] for m in movs)
                
                texto = f"📊 *ESTADO DE CUENTA*\n👤 Propietario: {nombre_usuario}\n✉️ Correo: {correo_usuario}\n💰 Capital Actual: *${total:.2f}*\n\n*Detalle de Movimientos:*\n"
                for m in movs:
                    signo = "+" if m[2] >= 0 else ""
                    texto += f"• {m[0]} | {m[1]}: {signo}${m[2]:.2f}\n"
                    
                texto_codificado = urllib.parse.quote(texto)
                tel_limpio = telefono_usuario.replace('+', '').replace(' ', '')
                
                # Invocación forzada a nivel del SO Android
                page.launch_url(f"whatsapp://send?phone={tel_limpio}&text={texto_codificado}")
            except Exception as e:
                notificar(f"Error abriendo WhatsApp", "red700")

        page.add(
            contenedor_balance,
            ft.Row([boton_fecha], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([entrada_concepto, entrada_monto]),
            ft.Row([
                ft.FilledButton("Ingreso", icon="add", style=ft.ButtonStyle(bgcolor="green600"), on_click=lambda e: agregar_movimiento(e, "ingreso"), expand=True),
                ft.FilledButton("Gasto", icon="remove", style=ft.ButtonStyle(bgcolor="red600"), on_click=lambda e: agregar_movimiento(e, "gasto"), expand=True)
            ]),
            ft.Divider(height=15, color="transparent"),
            ft.Text("HISTORIAL DE MOVIMIENTOS", weight=ft.FontWeight.BOLD, color="grey400", size=12),
            lista_historial, 
            ft.ElevatedButton(
                "Enviar mi Reporte por WhatsApp", 
                icon="share", 
                bgcolor="green500", 
                color="white",
                on_click=enviar_reporte,
                width=float('inf') 
            )
        )
        cargar_datos()

    # ==========================================
    # 5. CONTROL DE ACCESO INICIAL
    # ==========================================
    try:
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()
        cursor.execute("SELECT nombre, telefono, correo FROM perfil LIMIT 1")
        usuario_existente = cursor.fetchone()
        conexion.close()

        if usuario_existente:
            mostrar_principal(usuario_existente)
        else:
            mostrar_registro()
    except Exception as e:
        mostrar_registro()

ft.app(target=main)
