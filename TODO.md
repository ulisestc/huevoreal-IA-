# Checklist de Funcionalidades Pendientes (TODO)

Este documento recopila todas las funcionalidades operativas, comerciales y de configuración multi-tenant/marca blanca que fueron revertidas para mantener el sistema 100% fiel a su flujo funcional original mientras se aprueba la fase de comercialización.

---

## 1. Configuración de Marca Blanca y Multi-Granja

- [ ] **Variables en `settings.py` / `.env`:**
  - [ ] `APP_NAME`: Nombre configurable de la granja (por defecto `'Huevo Real'`).
  - [ ] `APP_LOGO`: Ruta a logotipo configurable para tickets y reportes.
- [ ] **Context Processor:**
  - [ ] Crear `huevoreal/context_processors.py` para inyectar `APP_NAME` en el contexto global de Django.
  - [ ] Registrar el procesador en `TEMPLATES['OPTIONS']['context_processors']`.
  - [ ] Reemplazar nombres fijos en `<title>`, navbar de `base.html` y encabezado de `login.html` por `{{ APP_NAME }}`.

---

## 2. Control de Acceso y Visibilidad del Módulo de Inversores

- [ ] **Flag de activación comercial:**
  - [ ] Variable `ENABLE_INVESTORS_MODULE` (booleano en `.env` / `settings.py`).
- [ ] **Protección a nivel de vista:**
  - [ ] Agregar validación en `sales/views.py` (`InvestorDashboardView.dispatch`) para retornar `Http404` o `PermissionDenied` si el módulo está desactivado para la cuenta o cliente.
- [ ] **Visibilidad en navegación:**
  - [ ] Condicionar la pestaña "Inversores" en `templates/base.html` para que solo aparezca si el módulo está activo y/o el usuario cuenta con el rol autorizado (`ADMIN`).

---

## 3. KPIs Operativos en Panel de Control (Dashboard)

- [ ] **Parvada y porcentaje de postura:**
  - [ ] Variable `TOTAL_BIRDS`: Número total de aves activas en la granja (ej. 5,000).
  - [ ] En `users/views.py` (`dashboard`), calcular la producción del día:
    `InventoryMovement.objects.filter(movement_type='PRODUCCION', date=today).aggregate(Sum('quantity'))`.
  - [ ] Calcular porcentaje de postura diario:
    `postura_pct = (huevos_hoy / TOTAL_BIRDS) * 100`.
- [ ] **Métricas rápidas de ventas y cobranza:**
  - [ ] Ingresos vendidos en la fecha actual (`day=today`).
  - [ ] Cartera vencida o saldo pendiente global acumulado.
- [ ] **Tarjetas de métricas en `dashboard.html`:**
  - [ ] Mostrar fila superior con KPIs de producción, postura %, ventas de hoy y cobranza pendiente con diseño editorial limpio.

---

## 4. Cobranza y Comprobantes por WhatsApp

- [ ] **Propiedad de saldo pendiente (`Sale`):**
  - [ ] En `sales/models.py`, agregar propiedad `pending_balance = max(Decimal('0.00'), self.price - self.amount_paid)`.
- [ ] **Generador de enlace de WhatsApp (`Sale`):**
  - [ ] En `sales/models.py`, agregar propiedad `whatsapp_url` utilizando `urllib.parse.quote` y el teléfono del cliente (`customer.phone`).
  - [ ] Formatear el mensaje con:
    - Folio de venta y fecha.
    - Cliente.
    - Detalle (Kilos o piezas vendidas y precio unitario).
    - Total, importe pagado y saldo pendiente.
    - Estado de la cuenta (PAGADO vs SALDO PENDIENTE).
- [ ] **Botón de acción en la interfaz:**
  - [ ] En `templates/sales/sale_list.html`, habilitar botón de WhatsApp con icono `fab fa-whatsapp` en la columna de acciones si el cliente tiene teléfono registrado.

---

## 5. Empaquetado y Distribución Comercial

- [ ] **Distribución local (sin consola ni Python visible):**
  - [ ] Crear ejecutable independiente (`.exe`) o script empaquetado con PyInstaller / WebView para clientes que requieran operación 100% local.
  - [ ] Rutina de inicialización automática de SQLite y migraciones.
  - [ ] Script de respaldo automático local diario de `db.sqlite3`.
- [ ] **Distribución en la nube (SaaS):**
  - [ ] Automatización de despliegue y separación de bases de datos por granja o aislamiento lógico multi-inquilino.
