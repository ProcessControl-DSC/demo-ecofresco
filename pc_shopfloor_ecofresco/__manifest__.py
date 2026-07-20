# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    "name": "PC Shop Floor - Fichaje de jornada",
    "summary": "Ficha entrada/salida de jornada (hr.attendance) automáticamente al conectar/desconectar el operario en Shop Floor, e imputa tiempo a tareas indirectas (Limpieza, Almacén) desde el propio panel",
    "version": "19.0.2.1.0",
    "category": "Manufacturing/Manufacturing",
    "author": "Process Control",
    "website": "https://www.processcontrol.es",
    "license": "LGPL-3",
    "depends": [
        "mrp_workorder",
        "hr_attendance",
        "project",
        "hr_timesheet",
    ],
    "data": [
        "views/project_project_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "pc_shopfloor_ecofresco/static/src/**/*.js",
            "pc_shopfloor_ecofresco/static/src/**/*.xml",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
    "description": """
<div style="font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; color: #1e293b; line-height: 1.6; max-width: 1000px;" data-oe-version="1.0">

  <h2 style="font-size: 20px; font-weight: 700; color: #1B72D3; margin: 32px 0 16px 0; padding-bottom: 8px; border-bottom: 3px solid #1B72D3;">PC Shop Floor - Fichaje de jornada</h2>
  <p style="font-size: 14px; color: #334155; margin-bottom: 10px;">Integra el fichaje de jornada (Asistencias) dentro de la app Shop Floor: cuando un operario se identifica con su PIN en el panel de operarios de Shop Floor, se registra automáticamente su entrada; cuando cierra sesión, se registra su salida. El operario no tiene que pasar por el kiosco de Asistencias ni fichar dos veces.</p>

  <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 10px 0 16px 0; font-size: 13px; color: #334155;">
    <p style="margin: 2px 0;"><strong>Decisión funcional asumida:</strong> se equipara el login de operario en Shop Floor a un fichaje de entrada, y el logout a un fichaje de salida. Es una decisión de negocio para la demo, no un comportamiento estándar de Odoo — debe validarse con el cliente antes de llevarla a producción, en particular si el operario puede quedar "conectado" en Shop Floor sin estar físicamente presente en el centro de trabajo.</p>
  </div>

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
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155;"><code>mrp_workorder</code></td>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155;">App Shop Floor: login/logout de operario por PIN (<code>hr.employee.login()</code> / <code>logout()</code>).</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; color: #334155;"><code>hr_attendance</code></td>
        <td style="padding: 10px 14px; color: #334155;">Modelo <code>hr.attendance</code> donde se registra el fichaje.</td>
      </tr>
    </tbody>
  </table>

  <h2 style="font-size: 17px; font-weight: 700; color: #1B72D3; margin: 28px 0 12px 0; padding-bottom: 6px; border-bottom: 2px solid #e2e8f0;">2. Flujo de uso</h2>
  <ul style="font-size: 14px; color: #334155; margin-bottom: 10px; padding-left: 24px;">
    <li style="margin-bottom: 6px;">El operario abre el panel de operarios de Shop Floor y se identifica con su PIN.</li>
    <li style="margin-bottom: 6px;">Si no tiene ya un fichaje abierto, se crea automáticamente un registro de asistencia con la hora de entrada.</li>
    <li style="margin-bottom: 6px;">Si ya está fichado (por ejemplo, ya conectado en Shop Floor o fichado por el kiosco de Asistencias), no se duplica el fichaje.</li>
    <li style="margin-bottom: 6px;">Al desconectarse del panel de operarios ("Logout"), si tiene un fichaje abierto se cierra con la hora de salida.</li>
    <li style="margin-bottom: 6px;">Convertirse en "propietario de sesión" (operario al mando) sin desconectar no genera un fichaje nuevo, solo el primer login del operario lo hace.</li>
  </ul>

  <h2 style="font-size: 17px; font-weight: 700; color: #1B72D3; margin: 28px 0 12px 0; padding-bottom: 6px; border-bottom: 2px solid #e2e8f0;">3. Advertencias técnicas</h2>
  <table style="width: 100%; border-collapse: separate; border-spacing: 0; margin: 14px 0 20px 0; font-size: 13px; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
    <thead>
      <tr>
        <th style="background: linear-gradient(180deg, #1B72D3 0%, #16294C 100%); color: white; font-weight: 600; padding: 10px 14px; text-align: left;">Aspecto</th>
        <th style="background: linear-gradient(180deg, #1B72D3 0%, #16294C 100%); color: white; font-weight: 600; padding: 10px 14px; text-align: left;">Detalle</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155;">Idempotencia</td>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155;">No se usa <code>attendance_manual</code> (alterna a ciegas); se comprueba siempre si existe un fichaje abierto antes de crear o cerrar uno.</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155; background: #f1f6fb;">Zona horaria</td>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155; background: #f1f6fb;">Fichajes en UTC servidor (<code>fields.Datetime.now()</code>), igual que el resto de Asistencias.</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; color: #334155;">Cierre de sesión sin logout</td>
        <td style="padding: 10px 14px; color: #334155;">Si el navegador se cierra sin pulsar "Logout" el fichaje queda abierto, igual que ocurriría con el kiosco de Asistencias; requiere cierre manual desde Asistencias.</td>
      </tr>
    </tbody>
  </table>

  <h2 style="font-size: 17px; font-weight: 700; color: #1B72D3; margin: 28px 0 12px 0; padding-bottom: 6px; border-bottom: 2px solid #e2e8f0;">4. Tareas indirectas (Limpieza, Almacén...)</h2>
  <p style="font-size: 14px; color: #334155; margin-bottom: 10px;">Añade a Shop Floor un botón "Tareas indirectas" junto al panel de centros de trabajo. Permite al operario imputar tiempo a tareas de proyecto que no son de producción (limpieza, almacén...) sin salir del panel, con un cronómetro en vivo, sin tener que pasar por el kiosco de Asistencias ni por el backend de Proyecto.</p>
  <ul style="font-size: 14px; color: #334155; margin-bottom: 10px; padding-left: 24px;">
    <li style="margin-bottom: 6px;">El operario pulsa "Tareas indirectas" y elige una tarea de la lista (solo aparecen tareas de proyectos marcados como "Tarea indirecta Shop Floor").</li>
    <li style="margin-bottom: 6px;">Se inicia un cronómetro en vivo (HH:MM:SS) con los botones "Finalizar" y "Cancelar".</li>
    <li style="margin-bottom: 6px;">"Finalizar" crea el parte de horas (<code>account.analytic.line</code>) para el operario conectado en Shop Floor (operario "al mando"), con las horas transcurridas. "Cancelar" descarta el cronómetro sin crear nada.</li>
    <li style="margin-bottom: 6px;">Los proyectos elegibles se marcan desde su ficha (Proyecto &gt; &lt;proyecto&gt; &gt; casilla "Tarea indirecta Shop Floor"). Al instalar el módulo se marcan automáticamente, si existen, los proyectos "Limpieza" y "Almacén" de esta demo.</li>
  </ul>

  <h2 style="font-size: 17px; font-weight: 700; color: #1B72D3; margin: 28px 0 12px 0; padding-bottom: 6px; border-bottom: 2px solid #e2e8f0;">5. Advertencias técnicas — Tareas indirectas</h2>
  <table style="width: 100%; border-collapse: separate; border-spacing: 0; margin: 14px 0 20px 0; font-size: 13px; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
    <thead>
      <tr>
        <th style="background: linear-gradient(180deg, #1B72D3 0%, #16294C 100%); color: white; font-weight: 600; padding: 10px 14px; text-align: left;">Aspecto</th>
        <th style="background: linear-gradient(180deg, #1B72D3 0%, #16294C 100%); color: white; font-weight: 600; padding: 10px 14px; text-align: left;">Detalle</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155;">Operario nunca confiado del cliente</td>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155;">El servidor resuelve el operario conectado leyendo <code>hr.employee.get_session_owner()</code> (sesión de Shop Floor), igual que el resto de escrituras de Shop Floor; el navegador nunca decide a qué empleado se imputa.</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155; background: #f1f6fb;">Tiempo calculado en servidor</td>
        <td style="padding: 10px 14px; border-bottom: 1px solid #e8ecf1; color: #334155; background: #f1f6fb;">El cliente envía los segundos transcurridos (cronómetro basado en <code>Date.now()</code> del navegador); el servidor los convierte a horas (<code>unit_amount</code>). No se manejan zonas horarias de cliente para la duración, solo para la fecha del apunte (<code>fields.Date.context_today</code>).</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; color: #334155;">Unidad de horas asumida</td>
        <td style="padding: 10px 14px; color: #334155;">Se asume que la codificación de partes de horas de la compañía está en horas (no en días), igual que el resto de imputaciones de esta demo (kiosco MES incluido).</td>
      </tr>
    </tbody>
  </table>

</div>
""",
}
