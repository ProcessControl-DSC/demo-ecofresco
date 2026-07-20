# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    "name": "PC MES Kiosk",
    "summary": "Imputación de horas a proyectos/tareas desde el kiosco de Asistencias (limpieza, almacén, indirectas)",
    "version": "19.0.2.0.0",
    "category": "Human Resources/Attendances",
    "author": "Process Control",
    "website": "https://www.processcontrol.es",
    "license": "LGPL-3",
    "depends": [
        "hr_attendance",
        "hr_timesheet",
        "project",
    ],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "hr_attendance.assets_public_attendance": [
            "pc_mes_kiosk/static/src/**/*",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "description": """
<div style="font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; color: #1e293b; line-height: 1.6; max-width: 1000px;" data-oe-version="2.0">

  <h2 style="font-size: 20px; font-weight: 700; color: #1B72D3; margin: 32px 0 16px 0; padding-bottom: 8px; border-bottom: 3px solid #1B72D3;">PC MES Kiosk</h2>
  <p style="font-size: 14px; color: #334155; margin-bottom: 10px;">Amplía el kiosco público de Asistencias (Kiosk Mode) de Odoo con una pantalla táctil de imputación de horas a proyectos y tareas indirectas — limpieza, almacén y demás trabajo que no pasa por producción. La producción y sus operaciones de fabricación se gestionan con Shop Floor nativo; este módulo cubre exactamente lo que Shop Floor no cubre.</p>

  <h2 style="font-size: 17px; font-weight: 700; color: #1B72D3; margin: 28px 0 12px 0; padding-bottom: 6px; border-bottom: 2px solid #e2e8f0;">1. Requisitos</h2>
  <table style="width: 100%; border-collapse: separate; border-spacing: 0; margin: 14px 0 20px 0; font-size: 13px; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
    <thead>
      <tr>
        <th style="background: linear-gradient(180deg, #1B72D3 0%, #16294C 100%); color: white; font-weight: 600; padding: 10px 14px; text-align: left;">Módulo</th>
        <th style="background: linear-gradient(180deg, #1B72D3 0%, #16294C 100%); color: white; font-weight: 600; padding: 10px 14px; text-align: left;">Motivo</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155;"><code>hr_attendance</code></td>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155;">Kiosco público de fichaje. Base obligatoria.</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155; background: #f1f6fb;"><code>hr_timesheet</code></td>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155; background: #f1f6fb;">Modelo <code>account.analytic.line</code> para el apunte de horas.</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; color: #334155;"><code>project</code></td>
        <td style="padding: 10px 14px; color: #334155;">Modelos <code>project.project</code> y <code>project.task</code>.</td>
      </tr>
    </tbody>
  </table>

  <h2 style="font-size: 17px; font-weight: 700; color: #1B72D3; margin: 28px 0 12px 0; padding-bottom: 6px; border-bottom: 2px solid #e2e8f0;">2. Configuración</h2>
  <p style="font-size: 14px; color: #334155; margin-bottom: 10px;">Ajustes &gt; Asistencias &gt; bloque "Kiosco MES — Imputación a proyecto":</p>
  <table style="width: 100%; border-collapse: separate; border-spacing: 0; margin: 14px 0 20px 0; font-size: 13px; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
    <thead>
      <tr>
        <th style="background: linear-gradient(180deg, #1B72D3 0%, #16294C 100%); color: white; font-weight: 600; padding: 10px 14px; text-align: left;">Opción</th>
        <th style="background: linear-gradient(180deg, #1B72D3 0%, #16294C 100%); color: white; font-weight: 600; padding: 10px 14px; text-align: left;">Descripción</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155;">Momento de la pregunta</td>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155;">Al fichar entrada o al fichar salida. Determina cuándo aparece la pantalla de selección.</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155; background: #f1f6fb;">Mostrar proyectos</td>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155; background: #f1f6fb;">Activa o desactiva el paso de selección de proyecto.</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; color: #334155;">Mostrar tareas</td>
        <td style="padding: 10px 14px; color: #334155;">Activa o desactiva el paso de selección de tarea dentro del proyecto elegido.</td>
      </tr>
    </tbody>
  </table>

  <h2 style="font-size: 17px; font-weight: 700; color: #1B72D3; margin: 28px 0 12px 0; padding-bottom: 6px; border-bottom: 2px solid #e2e8f0;">3. Flujo de uso</h2>
  <ul style="font-size: 14px; color: #334155; margin-bottom: 10px; padding-left: 24px;">
    <li style="margin-bottom: 6px;">El operario ficha con PIN o tarjeta en el kiosco público, como siempre.</li>
    <li style="margin-bottom: 6px;">Según el momento configurado, aparece la pantalla de selección de proyecto y, si procede, de tarea. También puede omitirse.</li>
    <li style="margin-bottom: 6px;">Confirmada la selección (o al omitirla), se muestra la pantalla de trabajo con un cronómetro en vivo (HH:MM:SS) y los botones "Pausa" y "Fichar salida", para no tener que volver a introducir el PIN.</li>
    <li style="margin-bottom: 6px;">Al fichar la salida, se crea automáticamente una línea de parte de horas (<code>account.analytic.line</code>) con las horas trabajadas, vinculada al registro de asistencia.</li>
  </ul>

  <h2 style="font-size: 17px; font-weight: 700; color: #1B72D3; margin: 28px 0 12px 0; padding-bottom: 6px; border-bottom: 2px solid #e2e8f0;">4. Modelos y campos</h2>
  <table style="width: 100%; border-collapse: separate; border-spacing: 0; margin: 14px 0 20px 0; font-size: 13px; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
    <thead>
      <tr>
        <th style="background: linear-gradient(180deg, #1B72D3 0%, #16294C 100%); color: white; font-weight: 600; padding: 10px 14px; text-align: left;">Campo (hr.attendance)</th>
        <th style="background: linear-gradient(180deg, #1B72D3 0%, #16294C 100%); color: white; font-weight: 600; padding: 10px 14px; text-align: left;">Descripción</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155;"><code>pc_project_id</code></td>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155;">Proyecto de imputación elegido en el kiosco.</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155; background: #f1f6fb;"><code>pc_task_id</code></td>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155; background: #f1f6fb;">Tarea de imputación elegida en el kiosco.</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; color: #334155;"><code>pc_timesheet_line_id</code></td>
        <td style="padding: 10px 14px; color: #334155;">Apunte de horas generado al fichar la salida (solo lectura, idempotente).</td>
      </tr>
    </tbody>
  </table>

  <h2 style="font-size: 17px; font-weight: 700; color: #1B72D3; margin: 28px 0 12px 0; padding-bottom: 6px; border-bottom: 2px solid #e2e8f0;">5. Endpoints públicos</h2>
  <p style="font-size: 14px; color: #334155; margin-bottom: 10px;"><code>POST /pc_mes_kiosk/targets</code> (proyectos, tareas y configuración) y <code>POST /pc_mes_kiosk/set_target</code> (guarda la selección y devuelve el estado del cronómetro). Ambos con <code>auth="public"</code>, igual que el resto del kiosco.</p>

  <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 10px 0 16px 0; font-size: 13px; color: #334155;">
    <p style="margin: 2px 0;">Este módulo no toca nada de producción, órdenes de fabricación ni pesada — eso vive en Shop Floor nativo. Un registro de asistencia admite un único proyecto y una única tarea; no reparte horas entre varios destinos.</p>
  </div>

</div>
""",
}
