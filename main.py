import flet as ft
import urllib.parse
from datetime import datetime

def main(page: ft.Page):
    # ==========================================
    # 1. CONFIGURACIÓN DE LA PÁGINA
    # ==========================================
    page.window.width = 380
    page.window.height = 680
    page.title = "Mi Balance"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.Colors.BLUE_GREY_900
    page.padding = 20

    # Lista en memoria para los registros (ideal para iniciar en blanco)
    # Nota: Aquí es donde más adelante puedes conectar tu INSERT/SELECT de SQLite
    movimientos = []

    # ==========================================
    # 2. UI - BALANCE PRINCIPAL
    # ==========================================
    texto_balance = ft.Text("$0.00", size=45, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    
    contenedor_balance = ft.Container(
        content=ft.Column([
            ft.Text("BALANCE ACTUAL", size=14, color=ft.Colors.WHITE70),
            texto_balance
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.Alignment.CENTER,
        padding=10
    )

    # ==========================================
    # 3. UI - HISTORIAL DE MOVIMIENTOS
    # ==========================================
    # Esta lista ocupará el espacio restante de la pantalla y será deslizable
    lista_historial = ft.ListView(expand=True, spacing=5)

    # ==========================================
    # 4. COMPONENTE DE FECHA (CALENDARIO)
    # ==========================================
    def cambiar_fecha(e):
        if selector_fecha.value:
            # Actualiza el texto del botón con la fecha seleccionada
            texto_fecha.value = selector_fecha.value.strftime("%d/%m/%Y")
            page.update()

    selector_fecha = ft.DatePicker(on_change=cambiar_fecha)
    page.overlay.append(selector_fecha)

    texto_fecha = ft.Text(datetime.now().strftime("%d/%m/%Y"))
    boton_fecha = ft.OutlinedButton(
        content=texto_fecha,
        icon=ft.Icons.CALENDAR_MONTH,
        on_click=lambda _: abrir_calendario()
    )

    def abrir_calendario():
        selector_fecha.open = True
        page.update()

    # ==========================================
    # 5. CAMPOS DE ENTRADA (INPUTS)
    # ==========================================
    entrada_concepto = ft.TextField(label="Concepto (Ej. Salario)", expand=True)
    entrada_monto = ft.TextField(label="Monto ($)", keyboard_type=ft.KeyboardType.NUMBER, width=110)

    # ==========================================
    # 6. LÓGICA DE LA APP
    # ==========================================
    def actualizar_ui():
        # 1. Calcular y mostrar el balance total
        total = sum(mov['monto'] for mov in movimientos)
        texto_balance.value = f"${total:.2f}"
        texto_balance.color = ft.Colors.RED_400 if total < 0 else ft.Colors.GREEN_400
        
        # 2. Actualizar la lista del historial visual
        lista_historial.controls.clear()
        
        # Invertimos la lista para mostrar el más reciente arriba
        for mov in reversed(movimientos): 
            es_ingreso = mov['monto'] >= 0
            icono = ft.Icons.ARROW_UPWARD if es_ingreso else ft.Icons.ARROW_DOWNWARD
            color_icono = ft.Colors.GREEN_400 if es_ingreso else ft.Colors.RED_400
            signo = "+" if es_ingreso else ""
            
            # Tarjeta de detalle para cada movimiento
            tarjeta = ft.ListTile(
                leading=ft.Icon(icono, color=color_icono),
                title=ft.Text(mov['concepto'], weight=ft.FontWeight.BOLD),
                subtitle=ft.Text(mov['fecha'], color=ft.Colors.WHITE54, size=12),
                trailing=ft.Text(f"{signo}${mov['monto']:.2f}", color=color_icono, weight=ft.FontWeight.BOLD, size=16)
            )
            lista_historial.controls.append(tarjeta)
            
        page.update()

    def agregar_movimiento(e, tipo):
        if not entrada_monto.value or not entrada_concepto.value:
            return # Evitar guardar si los campos están vacíos
            
        try:
            monto = float(entrada_monto.value.replace(",", "."))
            if tipo == "gasto":
                monto = -monto
            
            # Guardamos el detalle con la fecha seleccionada
            movimientos.append({
                "fecha": texto_fecha.value,
                "concepto": entrada_concepto.value, 
                "monto": monto
            })
            
            # Limpiamos los campos
            entrada_monto.value = ""
            entrada_concepto.value = ""
            actualizar_ui()
            
        except ValueError:
            pass # Ignorar si el usuario escribe letras en lugar de números

    def compartir_whatsapp(e):
        if not movimientos:
            return
            
        # Preparar el texto
        total = sum(mov['monto'] for mov in movimientos)
        texto = f"📊 *BALANCE ACTUAL*: ${total:.2f}\n\n*Detalles:*\n"
        
        for mov in movimientos:
            signo = "+" if mov['monto'] >= 0 else ""
            texto += f"• {mov['fecha']} | {mov['concepto']}: {signo}${mov['monto']:.2f}\n"
            
        # Codificar texto para URLs
        texto_codificado = urllib.parse.quote(texto)
        
        # Esquema nativo (Deep Link) para Android
        url_whatsapp_nativa = f"whatsapp://send?text={texto_codificado}"
        
        try:
            # Esto fuerza a Android a abrir la app directamente
            page.launch_url(url_whatsapp_nativa)
        except Exception:
            # Si el esquema nativo falla, intenta con la versión web como respaldo
            page.launch_url(f"https://wa.me/?text={texto_codificado}")

    # ==========================================
    # 7. CONSTRUCCIÓN FINAL
    # ==========================================
    fila_botones_accion = ft.Row([
        ft.FilledButton("Ingreso", icon=ft.Icons.ADD, bgcolor=ft.Colors.GREEN_600, on_click=lambda e: agregar_movimiento(e, "ingreso"), expand=True),
        ft.FilledButton("Gasto", icon=ft.Icons.REMOVE, bgcolor=ft.Colors.RED_600, on_click=lambda e: agregar_movimiento(e, "gasto"), expand=True)
    ])

    boton_whatsapp = ft.ElevatedButton(
        "Compartir por WhatsApp", 
        icon=ft.Icons.SHARE, 
        bgcolor=ft.Colors.GREEN_500, 
        color=ft.Colors.WHITE,
        on_click=compartir_whatsapp,
        width=float('inf') # Que ocupe todo el ancho disponible
    )

    page.add(
        contenedor_balance,
        ft.Row([boton_fecha], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([entrada_concepto, entrada_monto]),
        fila_botones_accion,
        ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
        ft.Text("HISTORIAL DE MOVIMIENTOS", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE54, size=12),
        lista_historial, # Se agrega la lista deslizable a la pantalla principal
        boton_whatsapp
    )
    
    actualizar_ui()

ft.run(main)
