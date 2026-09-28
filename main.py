import flet as ft
import urllib.parse

def main(page: ft.Page):
    # ==========================================
    # 1. CONFIGURACIÓN DE LA PÁGINA (Estilo Móvil)
    # ==========================================
    page.window.width = 380
    page.window.height = 680
    page.title = "Mi Balance"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.Colors.BLUE_GREY_900
    
    # Centrar los elementos en la pantalla
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # ==========================================
    # 2. VARIABLES DE ESTADO
    # ==========================================
    # Usaremos una lista temporal en memoria para este ejemplo limpio.
    # Luego puedes integrarlo nuevamente con SQLite si lo deseas.
    movimientos = []

    # ==========================================
    # 3. INTERFAZ GRÁFICA (UI)
    # ==========================================
    texto_balance = ft.Text("$0.00", size=50, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    
    entrada_concepto = ft.TextField(label="Concepto (Ej. Salario)", width=150)
    entrada_monto = ft.TextField(label="Monto ($)", keyboard_type=ft.KeyboardType.NUMBER, width=120)

    # ==========================================
    # 4. LÓGICA DE LA APLICACIÓN
    # ==========================================
    def actualizar_ui():
        # Calcular el balance total
        total = sum(mov['monto'] for mov in movimientos)
        texto_balance.value = f"${total:.2f}"
        
        # Cambiar el color dependiendo si es positivo o negativo
        if total < 0:
            texto_balance.color = ft.Colors.RED_400
        else:
            texto_balance.color = ft.Colors.GREEN_400
            
        page.update()

    def agregar_movimiento(e, tipo):
        if not entrada_monto.value or not entrada_concepto.value:
            return # Evitar campos vacíos
        
        try:
            # Convertimos comas a puntos por si acaso
            monto = float(entrada_monto.value.replace(",", "."))
            if tipo == "gasto":
                monto = -monto  # Convertir a negativo si es gasto
            
            movimientos.append({"concepto": entrada_concepto.value, "monto": monto})
            
            # Limpiar campos
            entrada_monto.value = ""
            entrada_concepto.value = ""
            actualizar_ui()
            
        except ValueError:
            # Aquí podrías poner un SnackBar notificando error de formato
            pass 

    def compartir_whatsapp(e):
        # 1. Preparar el texto que se enviará
        total = sum(mov['monto'] for mov in movimientos)
        texto = f"📊 *BALANCE ACTUAL*: ${total:.2f}\n\n*Detalles:*\n"
        
        if movimientos:
            for mov in movimientos:
                signo = "+" if mov['monto'] >= 0 else ""
                texto += f"• {mov['concepto']}: {signo}${mov['monto']:.2f}\n"
        else:
            texto += "Sin movimientos registrados."
            
        # 2. Codificar el texto para que la URL lo lea correctamente (espacios, saltos de línea, emojis)
        texto_codificado = urllib.parse.quote(texto)
        
        # 3. Crear el enlace universal de WhatsApp
        url_whatsapp = f"https://wa.me/?text={texto_codificado}"
        
        # 4. Ejecutar el enlace. En Android, esto abrirá la app nativa de WhatsApp.
        page.launch_url(url_whatsapp)

    # ==========================================
    # 5. CONSTRUCCIÓN Y RENDERIZADO
    # ==========================================
    fila_inputs = ft.Row([entrada_concepto, entrada_monto], alignment=ft.MainAxisAlignment.CENTER)
    
    fila_botones = ft.Row([
        ft.FilledButton("Ingreso", icon=ft.Icons.ADD, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600), on_click=lambda e: agregar_movimiento(e, "ingreso")),
        ft.FilledButton("Gasto", icon=ft.Icons.REMOVE, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600), on_click=lambda e: agregar_movimiento(e, "gasto"))
    ], alignment=ft.MainAxisAlignment.CENTER)

    boton_whatsapp = ft.ElevatedButton(
        "Compartir por WhatsApp", 
        icon=ft.Icons.SHARE, 
        bgcolor=ft.Colors.GREEN_500, 
        color=ft.Colors.WHITE,
        on_click=compartir_whatsapp
    )

    # Agregar los controles a la vista principal
    page.add(
        ft.Text("BALANCE / CAPITAL", size=16, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE70),
        texto_balance,
        ft.Divider(height=40, color=ft.Colors.TRANSPARENT),
        fila_inputs,
        fila_botones,
        ft.Divider(height=60, color=ft.Colors.TRANSPARENT),
        boton_whatsapp
    )

ft.run(main)
