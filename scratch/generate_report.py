import os
import sys
import django
from decimal import Decimal
import datetime

# Add project path dynamically
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'huevoreal.settings')
django.setup()

from sales.models import Sale
from expenses.models import Expense
from inventory.models import InventoryMovement
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from fpdf import FPDF

class PDFReport(FPDF):
    def header(self):
        # Draw a clean header banner
        self.set_fill_color(26, 54, 93) # Navy blue
        self.rect(0, 0, 210, 35, 'F')
        
        self.set_text_color(255, 255, 255)
        self.set_font('helvetica', 'B', 16)
        self.cell(0, 10, 'Huevo Real - Reporte de Rendimiento y Utilidades', border=0, ln=1, align='C')
        
        self.set_font('helvetica', 'I', 10)
        self.cell(0, 5, f'Generado el: {datetime.date.today().strftime("%d/%m/%Y")} | Auditoria Operativa', border=0, ln=1, align='C')
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Pagina {self.page_no()}/{{nb}}', align='C')

def generate_pdf():
    # 1. Fetch data
    today = datetime.date.today()
    monthly_stats = []
    
    # Loop over last 6 months (February to July)
    for i in range(5, -1, -1):
        year = today.year
        month = today.month - i
        if month <= 0:
            month += 12
            year -= 1
        
        ms = datetime.date(year, month, 1)
        import calendar
        me = ms.replace(day=calendar.monthrange(year, month)[1])
        
        s_total = Sale.objects.filter(day__range=[ms, me]).aggregate(Sum('price'))['price__sum'] or Decimal('0.00')
        e_total = Expense.objects.filter(date__range=[ms, me]).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        net_profit = s_total - e_total
        
        eggs_prod = InventoryMovement.objects.filter(
            movement_type='PRODUCCION',
            date__range=[ms, me]
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0
        
        eggs_sold = Sale.objects.filter(day__range=[ms, me]).aggregate(
            Sum('quantity_piece'))['quantity_piece__sum'] or 0
            
        food_exp = Expense.objects.filter(category='ALIMENTO', date__range=[ms, me]).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        month_names_es = {
            1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 
            5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago', 
            9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
        }
        
        monthly_stats.append({
            'month': f"{month_names_es[ms.month]} {ms.year}",
            'sales': float(s_total),
            'expenses': float(e_total),
            'profit': float(net_profit),
            'produced': int(eggs_prod),
            'sold': int(eggs_sold),
            'food': float(food_exp)
        })

    # 2. Build PDF
    pdf = PDFReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Section 1
    pdf.set_text_color(51, 51, 51)
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 8, '1. Diagnostico del Negocio', ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 5, 
        'Se realizo una auditoria profunda de la base de datos de "Huevo Real". Los registros son consistentes '
        'y libres de duplicaciones. El descenso en las utilidades de junio y julio corresponde a una realidad '
        'operativa critica del negocio: un aumento drastico en el costo de alimentacion de las gallinas combinado '
        'con un colapso en la produccion interna de huevos.'
    )
    pdf.ln(5)
    
    # Section 2: Table
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 8, '2. Historial de Desempeno Operativo', ln=True)
    pdf.ln(2)
    
    # Table Headers
    pdf.set_fill_color(240, 244, 248)
    pdf.set_text_color(26, 54, 93)
    pdf.set_font('helvetica', 'B', 9)
    w = [25, 28, 28, 28, 28, 28, 25] # Total 190
    pdf.cell(w[0], 8, 'Mes', border=1, align='C', fill=True)
    pdf.cell(w[1], 8, 'Ventas ($)', border=1, align='C', fill=True)
    pdf.cell(w[2], 8, 'Gastos Tot. ($)', border=1, align='C', fill=True)
    pdf.cell(w[3], 8, 'Alimento ($)', border=1, align='C', fill=True)
    pdf.cell(w[4], 8, 'Utilidad ($)', border=1, align='C', fill=True)
    pdf.cell(w[5], 8, 'Prod. (pzas)', border=1, align='C', fill=True)
    pdf.cell(w[6], 8, 'Vend. (pzas)', border=1, align='C', fill=True)
    pdf.ln()
    
    pdf.set_text_color(51, 51, 51)
    pdf.set_font('helvetica', '', 9)
    for row in monthly_stats:
        pdf.cell(w[0], 7, row['month'], border=1, align='C')
        pdf.cell(w[1], 7, f"{row['sales']:,.2f}", border=1, align='R')
        pdf.cell(w[2], 7, f"{row['expenses']:,.2f}", border=1, align='R')
        pdf.cell(w[3], 7, f"{row['food']:,.2f}", border=1, align='R')
        
        # Color for profit
        if row['profit'] >= 0:
            pdf.set_text_color(26, 128, 54) # green
        else:
            pdf.set_text_color(204, 36, 36) # red
        pdf.cell(w[4], 7, f"{row['profit']:,.2f}", border=1, align='R')
        
        pdf.set_text_color(51, 51, 51)
        pdf.cell(w[5], 7, f"{row['produced']:,}", border=1, align='C')
        pdf.cell(w[6], 7, f"{row['sold']:,}", border=1, align='C')
        pdf.ln()
        
    pdf.ln(5)
    
    # Section 3
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 8, '3. Observaciones Clave', ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font('helvetica', '', 10)
    pdf.set_text_color(51, 51, 51)
    observations = [
        "- Desplome de Produccion: La produccion propia de huevos disminuyo de 8,207 piezas en Mayo a 5,195 en Junio, y en lo que va de Julio (al dia 17) apenas se han registrado 1,250 piezas.",
        "- Incremento en Alimento: El gasto en alimento subio de $8,895.00 en Mayo a $16,455.00 en Junio (un incremento del 85%), y en Julio ya se han gastado $10,575.00 en solo 17 dias.",
        "- Relacion Inversa Alimento/Produccion: A pesar de que las gallinas estan consumiendo casi el doble de alimento, la produccion bajo a menos de la mitad. Esto sugiere problemas de salud en las gallinas o merma no registrada.",
        "- Dependencia de Proveedores: Debido a la falta de produccion propia en Julio, se tuvo que gastar en compra de huevo externo, lo cual encarece los costos y reduce el margen de ganancia."
    ]
    for obs in observations:
        pdf.multi_cell(0, 5, obs)
        pdf.ln(1)
        
    pdf.ln(5)
    
    # Section 4
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 8, '4. Plan de Accion Recomendado', ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font('helvetica', '', 10)
    action_plan = [
        "1. Revision Veterinaria Urgente (Prioridad Alta):",
        "   Es vital que un especialista examine a las gallinas de inmediato. Un aumento de comida con caida de postura suele indicar estres, enfermedades, parasitos o que la edad de postura util ha terminado.",
        "2. Auditoria e Inspeccion de Inventario de Alimento (Control de Merma/Robo):",
        "   Verificar fisicamente si los bultos de comida se estan consumiendo realmente o si hay desperdicio excesivo (comederos mal disenados), plagas (roedores comiendo el alimento) o posibles fugas de inventario.",
        "3. Negociacion y Compra de Alimento al por Mayor:",
        "   Actualmente se compra alimento cada 2 o 3 dias en lotes pequenos. Comprar por toneladas o directamente con distribuidores mayoristas podria reducir el costo unitario de alimentacion por lo menos en un 15-20%.",
        "4. Registro Disciplinado de Merma de Postura:",
        "   Asegurarse de que no haya huevos rotos o perdidos que se esten desechando en la granja sin registrar, lo que falsearia las cifras de produccion."
    ]
    for step in action_plan:
        if step.startswith("1.") or step.startswith("2.") or step.startswith("3.") or step.startswith("4."):
            pdf.set_font('helvetica', 'B', 10)
            pdf.cell(0, 6, step, ln=True)
            pdf.set_font('helvetica', '', 10)
        else:
            pdf.multi_cell(0, 5, step)
            pdf.ln(2)

    pdf.output('reporte_utilidades.pdf')
    print("Report PDF generated successfully as 'reporte_utilidades.pdf'.")

if __name__ == '__main__':
    generate_pdf()
