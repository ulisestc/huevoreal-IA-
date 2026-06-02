# Huevo Real — Contexto del Proyecto

Aplicación web para administrar el negocio de venta de huevo del **tío Paul**. Sirve para registrar ventas, gastos, inventario, pedidos y clientes. También tiene un dashboard de inversores con calculadora de ROI basada en datos reales.

---

## Stack

- **Backend:** Django 6.0
- **Base de datos:** SQLite (`db.sqlite3`)
- **Frontend:** Bootstrap 5.3.3 + Font Awesome 6 + Chart.js (CDN)
- **Autenticación:** Django Auth con modelo `CustomUser` (roles: `ADMIN`, `VENDEDOR`)
- **Static files:** Whitenoise
- **Virtualenv:** `.venv/` en la raíz del proyecto

## Cómo correr

```bash
.venv/bin/python manage.py runserver        # servidor de desarrollo
.venv/bin/python manage.py migrate          # migraciones
.venv/bin/python manage.py check            # verificar configuración
```

Siempre usar `.venv/bin/python`, nunca `python` directamente.

---

## Estructura de apps

| App         | Prefijo URL       | Responsabilidad                                  |
|-------------|-------------------|--------------------------------------------------|
| `users`     | `/`               | Login, logout, dashboard, registro de vendedores |
| `customers` | `/customers/`     | CRUD de clientes                                 |
| `inventory` | `/inventory/`     | Ubicaciones, movimientos, traspasos, correcciones|
| `sales`     | `/sales/`         | Ventas, pedidos, estadísticas, inversores        |
| `expenses`  | `/expenses/`      | Gastos con categoría y método de pago            |

---

## Modelos clave

### `users.CustomUser`
```python
role = CharField(choices=[('ADMIN','Admin Maestro'), ('VENDEDOR','Vendedor')])
```

### `sales.Sale`
```python
day             = DateField()
customer        = FK(Customer)
location        = FK(Location)          # de dónde se descuenta el inventario
sale_type       = CharField('KILO'|'PIEZA')
quantity_kg     = DecimalField(null=True)
quantity_piece  = IntegerField(null=True)
unit_price      = DecimalField()
price           = DecimalField()        # total
amount_paid     = DecimalField()
is_paid         = BooleanField()
payment_date    = DateField()
seller          = FK(CustomUser)
payment_method  = CharField('EFECTIVO'|'TRANSFERENCIA')
```

### `sales.Order`
Mismos campos que `Sale` + `status` (`PENDIENTE`/`COMPLETADO`/`CANCELADO`).
Al marcar como completado (`complete_order` view) se convierte en `Sale` y descuenta inventario.

### `inventory.InventoryMovement`
```python
location       = FK(Location)
quantity       = IntegerField()
movement_type  = CharField('PRODUCCION'|'VENTA'|'TRASPASO_ENTRADA'|'TRASPASO_SALIDA'|'CORRECCION')
merma          = IntegerField(default=0)
date           = DateTimeField(auto_now_add=True)  # ← se setea solo, no editable
```
- Producción de huevo → `movement_type='PRODUCCION'`
- Ventas de huevo → `movement_type='VENTA'` (se crea automáticamente al guardar una `Sale`)

### `expenses.Expense`
```python
description     = CharField()
amount          = DecimalField()
date            = DateField()           # ← editable, distinto a DateTimeField de InventoryMovement
category        = CharField('ALIMENTO'|'MEDICAMENTO'|'SUELDOS'|'TRANSPORTE'|'MANTENIMIENTO'|'TARJETA_CREDITO'|'OTROS')
payment_method  = CharField('EFECTIVO'|'TRANSFERENCIA'|'TARJETA_CREDITO')
user            = FK(CustomUser, null=True)
```

---

## URLs importantes

```
/                           → dashboard (login required)
/sales/                     → lista de ventas
/sales/create/              → nueva venta
/sales/statistics/          → estadísticas mensuales
/sales/orders/              → pedidos pendientes
/sales/inversores/          → dashboard de inversores + calculadora ROI
/expenses/                  → lista de gastos
/inventory/movements/       → movimientos de inventario (producción aquí)
/admin/                     → Django admin
```

---

## Estadísticas (`sales/views.py → StatisticsView`)

- Filtra por mes via query param `?month=YYYY-MM`
- Muestra: ventas, gastos, utilidad neta, **producción de huevo**, **huevos vendidos** (piezas + kg)
- Tabla histórica (últimos 12 meses): incluye columnas de huevo
- Gráficos: tendencia diaria, métodos de pago, top 5 clientes, producción vs ventas de huevo
- Los datos de producción vienen de `InventoryMovement.movement_type='PRODUCCION'` filtrados por `date__date__range`

## Dashboard de Inversores (`sales/views.py → InvestorDashboardView`)

- **Solo usa meses con AMBOS ventas Y gastos registrados** para calcular promedios y margen. Meses sin gastos (como enero en el historial actual) se excluyen de los KPIs para no inflar la utilidad.
- Muestra: ingreso promedio, utilidad promedio, margen %, crecimiento mensual, clientes únicos, huevos producidos
- Indicador de confiabilidad: rojo (<3 meses completos), amarillo (<6), verde (≥6)
- Calculadora de ROI en JavaScript: el usuario ingresa monto de inversión y % de utilidades; calcula retorno mensual, meses para recuperar, retorno año 1, ROI anual
- Todas las cifras vienen de la BD real — cero valores hardcodeados

---

## Reglas de negocio importantes

1. **Datos reales siempre.** Nunca hardcodear números. Si no hay datos, mostrar "Sin datos" o "Sin registro", no ceros.
2. **Meses incompletos fuera de KPIs.** Un mes sin gastos registrados no es representativo — excluirlo de promedios en el dashboard de inversores.
3. **Confiabilidad explícita.** Siempre mostrar cuántos meses de historial se usaron para las proyecciones.
4. **`InventoryMovement.date` es `auto_now_add`** — no se puede setear manualmente aunque el código lo intente en `SaleCreateView`. Al filtrar producción por mes, usar `date__date__gte` / `date__date__lte`.

---

## Frontend / CSS

- Archivo principal: `static/css/style.css`
- Colores: verde oscuro primario `#1e5128`, verde secundario `#4e9f3d`
- Mobile-first: breakpoint en 768px, botones full-width en móvil, `font-size: 16px` en forms para evitar zoom en iOS
- Tablas con `table-responsive` + scroll horizontal en móvil
- Charts con `max-height: 350px` (220px en móvil <576px)
- Templates en `templates/<app>/`

---

## Contexto del negocio

- Vendedor de huevo en México
- Registra ventas por **kilo** o por **pieza**
- Clientes tienen pedidos recurrentes (flujo: Pedido → completar → Venta)
- El dueño (Paul) quiere mostrar el negocio a inversores potenciales
- Los datos son reales y se usarán en presentaciones — precisión crítica
