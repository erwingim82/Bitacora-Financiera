import flet as ft
import sqlite3
import os
from pathlib import Path
from datetime import datetime
import urllib.parse

def main(page: ft.Page):
    page.window.width = 380
    page.window.height = 680
    page.title = "Bitácora Financiera"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.Colors.BLUE_GREY_900
    page.padding = 0

    # ==========================================
    # 1. BASE DE DATOS BLINDADA (PATHLIB)
    # ==========================================
    try:
        if page.platform == ft.PagePlatform.ANDROID or page.platform == ft.PagePlatform.IOS:
            directorio_base = Path(page.get_user_data_dir())
        else:
            directorio_base = Path(os.getcwd())
            
        directorio_base.mkdir(parents=True, exist_ok=True)
        DB_NAME = str(directorio_base / "bitacora_financiera.db")
    except:
        DB_NAME = "bitacora_respaldo.db"

    def inicializar_bd():
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS movimientos (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            fecha TEXT,
                            concepto TEXT,
                            monto REAL,
                            tipo TEXT
                          )''')
        conexion.commit()
        conexion.close()
        
    inicializar_bd()

    def notificar(mensaje, color=ft.Colors.GREEN_700):
        snack = ft.SnackBar(ft.Text(mensaje, color=ft.Colors.WHITE), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # ==========================================
    # 2. DIÁLOGO "ACERCA DE" Y SUGERENCIAS
    # ==========================================
    dialogo_acerca = ft.AlertDialog(
        title=ft.Text("Acerca de", weight=ft.FontWeight.BOLD),
        content=ft.Column([
            ft.Text("Bitácora Financiera\nVersión V1.3\n\nControl de ingresos y egresos personales.", size=14, text_align=ft.TextAlign.CENTER),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            ft.TextButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.EMAIL, color=ft.Colors.BLUE_400), 
                    ft.Text("Enviar Sugerencia / Soporte", color=ft.Colors.BLUE_400)
                ], alignment=ft.MainAxisAlignment.CENTER, tight=True), 
                on_click=lambda e: page.launch_url("mailto:myconsultingsca@gmail.com?subject=Sugerencias%20Bitacora%20Financiera")
            )
        ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        actions=[ft.TextButton("Cerrar", on_click=lambda e: setattr(dialogo_acerca, "open", False) or page.update())]
    )
    page.overlay.append(dialogo_acerca)

    # ==========================================
    # 3. FUNCIONES DE ACCIÓN SUPERIOR (DIÁLOGOS MÓVILES SEGUROS)
    # ==========================================
    def mostrar_opciones_compartir(e):
        try:
            conexion = sqlite3.connect(DB_NAME)
            cursor = conexion.cursor()
            cursor.execute("SELECT fecha, concepto, monto, tipo FROM movimientos ORDER BY id ASC")
            movimientos = cursor.fetchall()
            conexion.close()

            saldo_total = 0.0
            texto_movimientos = ""

            if movimientos:
                for mov in movimientos:
                    fecha, concepto, monto, tipo = mov
                    es_ingreso = (tipo == "Depósito")
                    signo = "+" if es_ingreso else "-"
                    
                    if es_ingreso:
                        saldo_total += monto
                    else:
                        saldo_total -= monto
                        
                    texto_movimientos += f"• {fecha} | {concepto}: {signo}${monto:.2f}\n"
            else:
                texto_movimientos = "Sin movimientos registrados.\n"

            reporte = f"📊 *BITÁCORA FINANCIERA*\n💰 Saldo Actual: *${saldo_total:.2f}*\n\n*HISTORIAL DE MOVIMIENTOS:*\n{texto_movimientos}"
            reporte_codificado = urllib.parse.quote(reporte)
            url_whatsapp = f"https://api.whatsapp.com/send?text={reporte_codificado}"

            dialogo_compartir = ft.AlertDialog(
                title=ft.Text("Exportar Reporte", weight=ft.FontWeight.BOLD),
                content=ft.Column([
                    ft.Text("Selecciona una opción para enviar tu bitácora:", size=13, color=ft.Colors.WHITE_70),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.ElevatedButton(
                        "Enviar por WhatsApp",
                        icon=ft.Icons.SHARE,
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.GREEN_600,
                        on_click=lambda _: page.launch_url(url_whatsapp)
                    )
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                actions=[ft.TextButton("Cerrar", on_click=lambda _: setattr(dialogo_compartir, "open", False) or page.update())]
            )
            page.overlay.append(dialogo_compartir)
            dialogo_compartir.open = True
            page.update()

        except Exception as ex:
            notificar(f"Error al generar reporte: {ex}", ft.Colors.RED_700)

    def abrir_dolar_vzla(e):
        dialogo_dolar = ft.AlertDialog(
            title=ft.Text("Consulta de Tasas", weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Text("Haz clic en el botón para consultar las tasas actualizadas en DolarVzla.", size=13),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.ElevatedButton(
                    "Ir a DolarVzla.com",
                    icon=ft.Icons.OPEN_IN_BROWSER,
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.BLUE_600,
                    on_click=lambda _: page.launch_url("https://www.dolarvzla.com/")
                )
            ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[ft.TextButton("Cerrar", on_click=lambda _: setattr(dialogo_dolar, "open", False) or page.update())]
        )
        page.overlay.append(dialogo_dolar)
        dialogo_dolar.open = True
        page.update()

    # ==========================================
    # 4. INTERFAZ PRINCIPAL
    # ==========================================
    page.appbar = ft.AppBar(
        title=ft.Text("Mi Bitácora", weight=ft.FontWeight.BOLD),
        center_title=True,
        bgcolor=ft.Colors.BLUE_GREY_800,
        elevation=5,
        actions=[
            ft.IconButton(
                icon=ft.Icons.SHARE,
                icon_color=ft.Colors.GREEN_400,
                tooltip="Exportar por WhatsApp",
                on_click=mostrar_opciones_compartir
            ),
            ft.IconButton(
                icon=ft.Icons.CURRENCY_EXCHANGE,
                icon_color=ft.Colors.BLUE_400,
                tooltip="Consultar DolarVzla",
                on_click=abrir_dolar_vzla
            ),
            ft.IconButton(
                icon=ft.Icons.INFO_OUTLINE,
                icon_color=ft.Colors.ORANGE_400,
                tooltip="Acerca de y Sugerencias",
                on_click=lambda e: setattr(dialogo_acerca, "open", True) or page.update()
            )
        ]
    )

    texto_saldo = ft.Text("$0.00", size=36, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    tarjeta_saldo = ft.Container(
        content=ft.Column(
            [
                ft.Text("SALDO ACTUAL", size=14, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE_70),
                texto_saldo
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        bgcolor=ft.Colors.GREEN_700,
        border_radius=15,
        padding=20,
        margin=15, 
        alignment=ft.Alignment.CENTER,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.BLACK_38)
    )

    lista_movimientos = ft.ListView(expand=True, spacing=5, padding=15)

    def cargar_datos():
        lista_movimientos.controls.clear()
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()
        
        cursor.execute("SELECT id, fecha, concepto, monto, tipo FROM movimientos ORDER BY id DESC")
        movimientos = cursor.fetchall()
        
        saldo_total = 0.0
        
        if not movimientos:
            lista_movimientos.controls.append(
                ft.Container(
                    content=ft.Text("No hay registros todavía.\n¡Presiona el botón + para empezar!", 
                                    text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE_54),
                    alignment=ft.Alignment.CENTER,
                    padding=50
                )
            )
        else:
            for mov in movimientos:
                id_mov, fecha, concepto, monto, tipo = mov
                
                es_ingreso = (tipo == "Depósito")
                color_icono = ft.Colors.GREEN_400 if es_ingreso else ft.Colors.RED_400
                icono = ft.Icons.ARROW_UPWARD if es_ingreso else ft.Icons.ARROW_DOWNWARD
                signo = "+" if es_ingreso else "-"
                
                if es_ingreso:
                    saldo_total += monto
                else:
                    saldo_total -= monto

                lista_movimientos.controls.append(
                    ft.Card(
                        elevation=2,
                        bgcolor=ft.Colors.BLUE_GREY_800,
                        content=ft.ListTile(
                            leading=ft.CircleAvatar(content=ft.Icon(icono, color=color_icono), bgcolor=ft.Colors.BLUE_GREY_900),
                            title=ft.Text(concepto, weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(fecha, size=12, color=ft.Colors.WHITE_54),
                            trailing=ft.Text(f"{signo} ${monto:.2f}", color=color_icono, weight=ft.FontWeight.BOLD, size=16)
                        )
                    )
                )
                
        conexion.close()
        
        texto_saldo.value = f"${saldo_total:.2f}"
        
        if saldo_total < 0:
            tarjeta_saldo.bgcolor = ft.Colors.RED_800
        else:
            tarjeta_saldo.bgcolor = ft.Colors.GREEN_700
            
        page.update()

    # ==========================================
    # 5. DIÁLOGO PARA NUEVO REGISTRO
    # ==========================================
    entrada_monto = ft.TextField(label="Monto ($)", keyboard_type=ft.KeyboardType.NUMBER, prefix_icon=ft.Icons.ATTACH_MONEY)
    entrada_concepto = ft.TextField(label="Concepto (Ej: Sueldos y salarios)", capitalization=ft.TextCapitalization.SENTENCES, prefix_icon=ft.Icons.TEXT_SNIPPET)
    
    def cambiar_fecha(e):
        if selector_fecha.value:
            texto_fecha_boton.value = selector_fecha.value.strftime("%d/%m/%Y")
            page.update()

    selector_fecha = ft.DatePicker(
        first_date=datetime(2020, 1, 1),
        last_date=datetime(2030, 12, 31),
        on_change=cambiar_fecha
    )
    page.overlay.append(selector_fecha)

    texto_fecha_boton = ft.Text(datetime.now().strftime("%d/%m/%Y"))
    boton_fecha = ft.OutlinedButton(
        content=texto_fecha_boton,
        icon=ft.Icons.CALENDAR_MONTH,
        on_click=lambda e: setattr(selector_fecha, "open", True) or selector_fecha.update()
    )

    def guardar_registro(tipo_operacion):
        if not entrada_monto.value or not entrada_concepto.value:
            return notificar("Por favor completa el monto y el concepto.", ft.Colors.ORANGE_700)
            
        try:
            monto = float(entrada_monto.value.replace(",", "."))
        except ValueError:
            return notificar("Monto numérico inválido.", ft.Colors.RED_700)
            
        fecha_registro = texto_fecha_boton.value
        concepto = entrada_concepto.value

        try:
            conexion = sqlite3.connect(DB_NAME)
            cursor = conexion.cursor()
            cursor.execute("INSERT INTO movimientos (fecha, concepto, monto, tipo) VALUES (?, ?, ?, ?)", 
                           (fecha_registro, concepto, monto, tipo_operacion))
            conexion.commit()
            conexion.close()
            
            dialogo_nuevo.open = False
            page.update()
            
            notificar(f"{tipo_operacion} de ${monto:.2f} registrado con éxito.", ft.Colors.BLUE_700)
            
            entrada_monto.value = ""
            entrada_concepto.value = ""
            texto_fecha_boton.value = datetime.now().strftime("%d/%m/%Y")
            
            cargar_datos()
        except Exception as ex:
            notificar(f"Error al guardar en BD: {ex}", ft.Colors.RED_700)

    boton_deposito = ft.FilledButton("Depósito", icon=ft.Icons.ADD_CIRCLE, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600), on_click=lambda e: guardar_registro("Depósito"), expand=True)
    boton_gasto = ft.FilledButton("Gasto", icon=ft.Icons.REMOVE_CIRCLE, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600), on_click=lambda e: guardar_registro("Gasto"), expand=True)

    dialogo_nuevo = ft.AlertDialog(
        title=ft.Text("Nuevo Registro"),
        content=ft.Column(
            [
                entrada_concepto,
                entrada_monto,
                ft.Row([ft.Text("Fecha:", weight=ft.FontWeight.W_500), boton_fecha], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Row([boton_deposito, boton_gasto], spacing=10)
            ],
            tight=True
        ),
        actions=[ft.TextButton("Cancelar", on_click=lambda e: setattr(dialogo_nuevo, "open", False) or page.update())],
        actions_alignment=ft.MainAxisAlignment.END
    )
    
    page.overlay.append(dialogo_nuevo)

    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD,
        bgcolor=ft.Colors.BLUE_500,
        on_click=lambda e: setattr(dialogo_nuevo, "open", True) or page.update()
    )

    # ==========================================
    # 6. CONSTRUCCIÓN FINAL DE LA PÁGINA
    # ==========================================
    page.add(
        ft.Column(
            [
                tarjeta_saldo,
                ft.Container(
                    content=ft.Text("HISTORIAL DE MOVIMIENTOS", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE_54),
                    padding=10
                ),
                lista_movimientos
            ],
            expand=True
        )
    )

    cargar_datos()

ft.run(main)
