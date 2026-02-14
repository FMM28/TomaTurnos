import io
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import tempfile
import os
import re
from datetime import datetime
from sqlalchemy import func, case, and_
from app import db
from app.models import Ticket, TicketTramite, Atencion, Tramite, Usuario, Area
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, PageBreak, Image as RLImage
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER


class ReportService:

    ESTADO_FINALIZADO = "finalizado"
    ESTADO_CANCELADO = "cancelado"
    ESTADO_REASIGNADO = "reasignado"

    @staticmethod
    def _format_header_text(text):
        """Format header text: replace underscores with spaces and title case"""
        if not isinstance(text, str):
            return text
        return text.replace('_', ' ').title()

    @staticmethod
    def generar_reporte(
        fecha_inicio,
        fecha_fin,
        area_id=None,
        modo="tramites",
        exportar="excel",
        metricas_config=None
    ):
        """
        Genera reportes estadísticos de atenciones
        
        Args:
            fecha_inicio: Fecha inicio del periodo
            fecha_fin: Fecha fin del periodo
            area_id: ID del área (opcional)
            modo: 'tramites', 'usuarios', 'ambos'
            exportar: 'excel' o 'pdf'
            metricas_config: Dict con configuración de métricas a incluir
        """
        filtros = ReportService._build_filters(
            fecha_inicio,
            fecha_fin,
            area_id
        )

        if metricas_config is None:
            metricas_config = {
                'incluir_resumen': True,
                'incluir_estadisticas_base': True,
                'incluir_tiempos': True,
                'incluir_estados': True,
                'incluir_horas_pico': True,
                'incluir_horas_pico_semanal': True,
                'incluir_top_tramites': True,
                'incluir_top_usuarios': True,
                'incluir_tabla_cruzada': False,
            }

        data = {}
        metadata = {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'area_id': area_id,
            'modo': modo,
            'metricas_config': metricas_config
        }

        # Resumen general
        if metricas_config.get('incluir_resumen', True):
            data["resumen_general"] = ReportService._resumen_general(filtros)

        # Estadísticas base
        if metricas_config.get('incluir_estadisticas_base', True):
            if modo in ("tramites", "ambos"):
                data["tramites"] = ReportService._stats_por_tramite(filtros)
            if modo in ("usuarios", "ambos"):
                data["usuarios"] = ReportService._stats_por_usuario(filtros)

        # Horas pico
        if metricas_config.get('incluir_horas_pico', True):
            data["horas_pico"] = ReportService._horas_pico(filtros)
        
        if metricas_config.get('incluir_horas_pico_semanal', True):
            data["horas_pico_dia"] = ReportService._horas_pico_por_dia(filtros)

        if exportar == "excel":
            return ReportService._exportar_excel(data, metadata, filtros)

        return ReportService._exportar_pdf(data, metadata, filtros)

    @staticmethod
    def _build_filters(fecha_inicio, fecha_fin, area_id):
        filtros = []
        if fecha_inicio:
            filtros.append(Atencion.hora_inicio >= fecha_inicio)
        if fecha_fin:
            filtros.append(Atencion.hora_inicio <= fecha_fin)
        if area_id:
            filtros.append(Usuario.area_id == area_id)
        return filtros

    @staticmethod
    def _stats_por_tramite(filtros):
        query = (
            db.session.query(
                TicketTramite.id_tramite,
                Tramite.name.label('nombre_tramite'),
                func.count(Atencion.id_atencion).label('total_atenciones'),
                func.sum(case((Atencion.estado == ReportService.ESTADO_FINALIZADO, 1), else_=0)).label('finalizadas'),
                func.sum(case((Atencion.estado == ReportService.ESTADO_REASIGNADO, 1), else_=0)).label('reasignadas'),
                func.sum(case((Atencion.estado == ReportService.ESTADO_CANCELADO, 1), else_=0)).label('canceladas'),
                func.avg(func.timestampdiff(db.text("SECOND"), Atencion.hora_inicio, Atencion.hora_fin)).label('tiempo_promedio_segundos')
            )
            .join(TicketTramite, TicketTramite.id_ticket_tramite == Atencion.id_ticket_tramite)
            .join(Tramite, Tramite.id_tramite == TicketTramite.id_tramite)
            .join(Ticket, Ticket.id_ticket == TicketTramite.id_ticket)
            .join(Usuario, Usuario.id_usuario == Atencion.id_usuario)
            .filter(and_(*filtros))
            .group_by(TicketTramite.id_tramite, Tramite.name)
        )

        df = pd.DataFrame(query.all(), columns=[
            'id_tramite', 'nombre_tramite', 'total_atenciones', 
            'finalizadas', 'reasignadas', 'canceladas', 'tiempo_promedio_segundos'
        ])

        if not df.empty:
            df['tiempo_promedio_minutos'] = (df['tiempo_promedio_segundos'] / 60).round(2)
            df = df.fillna(0)
        return df

    @staticmethod
    def _stats_por_usuario(filtros):
        query = (
            db.session.query(
                Atencion.id_usuario,
                Usuario.username.label('username'),
                func.concat(Usuario.nombre, ' ', Usuario.ap_paterno, ' ', func.coalesce(Usuario.ap_materno, '')).label('nombre_completo'),
                func.count(Atencion.id_atencion).label('total_atenciones'),
                func.sum(case((Atencion.estado == ReportService.ESTADO_FINALIZADO, 1), else_=0)).label('finalizadas'),
                func.sum(case((Atencion.estado == ReportService.ESTADO_REASIGNADO, 1), else_=0)).label('reasignadas'),
                func.sum(case((Atencion.estado == ReportService.ESTADO_CANCELADO, 1), else_=0)).label('canceladas'),
                func.avg(func.timestampdiff(db.text("SECOND"), Atencion.hora_inicio, Atencion.hora_fin)).label('tiempo_promedio_segundos')
            )
            .join(Usuario, Usuario.id_usuario == Atencion.id_usuario)
            .join(TicketTramite, TicketTramite.id_ticket_tramite == Atencion.id_ticket_tramite)
            .join(Ticket, Ticket.id_ticket == TicketTramite.id_ticket)
            .filter(and_(*filtros))
            .group_by(Atencion.id_usuario, Usuario.username, 'nombre_completo')
        )

        df = pd.DataFrame(query.all(), columns=[
            'id_usuario', 'username', 'nombre_completo', 'total_atenciones',
            'finalizadas', 'reasignadas', 'canceladas', 'tiempo_promedio_segundos'
        ])

        if not df.empty:
            df['tiempo_promedio_minutos'] = (df['tiempo_promedio_segundos'] / 60).round(2)
            df = df.fillna(0)
            df['nombre_completo'] = df['nombre_completo'].str.strip()
        return df

    @staticmethod
    def _tabla_cruzada_global(filtros):
        """Matriz completa empleado x trámite (solo para Excel)"""
        query = (
            db.session.query(
                func.concat(Usuario.nombre, ' ', Usuario.ap_paterno, ' ', func.coalesce(Usuario.ap_materno, '')).label('empleado'),
                Tramite.name.label('tramite'),
                func.count(Atencion.id_atencion).label('total')
            )
            .join(Usuario, Usuario.id_usuario == Atencion.id_usuario)
            .join(TicketTramite, TicketTramite.id_ticket_tramite == Atencion.id_ticket_tramite)
            .join(Tramite, Tramite.id_tramite == TicketTramite.id_tramite)
            .join(Ticket, Ticket.id_ticket == TicketTramite.id_ticket)
            .filter(and_(*filtros))
            .group_by('empleado', Tramite.name)
        )

        df = pd.DataFrame(query.all(), columns=['empleado', 'tramite', 'total'])
        if df.empty:
            return pd.DataFrame()
        df['empleado'] = df['empleado'].str.strip()
        tabla = pd.pivot_table(df, values='total', index='empleado', columns='tramite', fill_value=0, aggfunc='sum')
        return tabla

    @staticmethod
    def _tramites_por_empleado(filtros):
        """Devuelve dict: {empleado: DataFrame(tramite, total)}"""
        query = (
            db.session.query(
                func.concat(Usuario.nombre, ' ', Usuario.ap_paterno, ' ', func.coalesce(Usuario.ap_materno, '')).label('empleado'),
                Tramite.name.label('tramite'),
                func.count(Atencion.id_atencion).label('total')
            )
            .join(Usuario, Usuario.id_usuario == Atencion.id_usuario)
            .join(TicketTramite, TicketTramite.id_ticket_tramite == Atencion.id_ticket_tramite)
            .join(Tramite, Tramite.id_tramite == TicketTramite.id_tramite)
            .join(Ticket, Ticket.id_ticket == TicketTramite.id_ticket)
            .filter(and_(*filtros))
            .group_by('empleado', Tramite.name)
            .order_by('empleado', Tramite.name)
        )
        
        df = pd.DataFrame(query.all(), columns=['empleado', 'tramite', 'total'])
        if df.empty:
            return {}
        
        empleado_dict = {}
        for empleado, group in df.groupby('empleado'):
            empleado_dict[empleado] = group[['tramite', 'total']].sort_values('total', ascending=False)
        return empleado_dict

    @staticmethod
    def _horas_pico(filtros):
        query = (
            db.session.query(
                func.hour(Atencion.hora_inicio).label('hora'),
                func.count(Atencion.id_atencion).label('total')
            )
            .join(TicketTramite, TicketTramite.id_ticket_tramite == Atencion.id_ticket_tramite)
            .join(Ticket, Ticket.id_ticket == TicketTramite.id_ticket)
            .join(Usuario, Usuario.id_usuario == Atencion.id_usuario)
            .filter(and_(*filtros))
            .group_by('hora')
            .order_by('hora')
        )

        df = pd.DataFrame(query.all(), columns=['hora', 'total'])
        if not df.empty:
            df['hora'] = df['hora'].astype(int)
        return df

    @staticmethod
    def _horas_pico_por_dia(filtros):
        query = (
            db.session.query(
                func.dayofweek(Atencion.hora_inicio).label('dia_semana'),
                func.hour(Atencion.hora_inicio).label('hora'),
                func.count(Atencion.id_atencion).label('total')
            )
            .join(TicketTramite, TicketTramite.id_ticket_tramite == Atencion.id_ticket_tramite)
            .join(Ticket, Ticket.id_ticket == TicketTramite.id_ticket)
            .join(Usuario, Usuario.id_usuario == Atencion.id_usuario)
            .filter(and_(*filtros))
            .group_by('dia_semana', 'hora')
        )

        df = pd.DataFrame(query.all(), columns=['dia_semana', 'hora', 'total'])
        if not df.empty:
            dias_map = {1: 'Domingo', 2: 'Lunes', 3: 'Martes', 4: 'Miércoles', 5: 'Jueves', 6: 'Viernes', 7: 'Sábado'}
            df['dia_nombre'] = df['dia_semana'].map(dias_map)
            df['hora'] = df['hora'].astype(int)
        return df

    @staticmethod
    def _resumen_general(filtros):
        query = (
            db.session.query(
                func.count(Atencion.id_atencion).label('total_atenciones'),
                func.sum(case((Atencion.estado == ReportService.ESTADO_FINALIZADO, 1), else_=0)).label('finalizadas'),
                func.sum(case((Atencion.estado == ReportService.ESTADO_REASIGNADO, 1), else_=0)).label('reasignadas'),
                func.sum(case((Atencion.estado == ReportService.ESTADO_CANCELADO, 1), else_=0)).label('canceladas'),
                func.avg(func.timestampdiff(db.text("SECOND"), Atencion.hora_inicio, Atencion.hora_fin)).label('tiempo_promedio_segundos'),
                func.count(func.distinct(Atencion.id_usuario)).label('usuarios_activos'),
                func.count(func.distinct(TicketTramite.id_tramite)).label('tramites_distintos')
            )
            .join(TicketTramite, TicketTramite.id_ticket_tramite == Atencion.id_ticket_tramite)
            .join(Ticket, Ticket.id_ticket == TicketTramite.id_ticket)
            .join(Usuario, Usuario.id_usuario == Atencion.id_usuario)
            .filter(and_(*filtros))
        )

        result = query.first()
        if result:
            return {
                'total_atenciones': result.total_atenciones or 0,
                'finalizadas': result.finalizadas or 0,
                'reasignadas': result.reasignadas or 0,
                'canceladas': result.canceladas or 0,
                'tiempo_promedio_minutos': round((result.tiempo_promedio_segundos or 0) / 60, 2),
                'usuarios_activos': result.usuarios_activos or 0,
                'tramites_distintos': result.tramites_distintos or 0
            }
        return {}

    @staticmethod
    def _exportar_excel(data, metadata, filtros):
        output = io.BytesIO()
        wb = Workbook()
        wb.remove(wb.active)

        header_font = Font(bold=True, color='FFFFFF', size=11)
        header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

        # Resumen
        if 'resumen_general' in data and data['resumen_general']:
            ws = wb.create_sheet('Resumen General')
            ws['A1'] = 'RESUMEN GENERAL'
            ws['A1'].font = Font(bold=True, size=14)
            row = 3
            for key, value in data['resumen_general'].items():
                ws[f'A{row}'] = ReportService._format_header_text(key)  # Formatted header
                ws[f'B{row}'] = value
                ws[f'A{row}'].font = Font(bold=True)
                row += 1

        # Tramites
        if 'tramites' in data and not data['tramites'].empty:
            ws = wb.create_sheet('Estadísticas por Trámite')
            ReportService._write_dataframe_to_sheet(ws, data['tramites'], header_font, header_fill, border)

        # Usuarios
        if 'usuarios' in data and not data['usuarios'].empty:
            ws = wb.create_sheet('Estadísticas por Usuario')
            ReportService._write_dataframe_to_sheet(ws, data['usuarios'], header_font, header_fill, border)

        # Matriz global
        if data.get('metricas_config', {}).get('incluir_tabla_cruzada', False):
            tabla_global = ReportService._tabla_cruzada_global(filtros)
            if not tabla_global.empty:
                ws = wb.create_sheet('Matriz Empleado-Trámite')
                ReportService._write_dataframe_to_sheet(ws, tabla_global, header_font, header_fill, border, include_index=True)

        # Hojas individuales por empleado
        tramites_por_emp = ReportService._tramites_por_empleado(filtros)
        for empleado, df_emp in tramites_por_emp.items():
            sheet_name = re.sub(r'[\\/*?:"<>|]', "_", empleado)[:30]
            ws_emp = wb.create_sheet(sheet_name)
            ReportService._write_dataframe_to_sheet(ws_emp, df_emp, header_font, header_fill, border)

        # Horas pico
        if 'horas_pico' in data and not data['horas_pico'].empty:
            ws = wb.create_sheet('Horas Pico')
            ReportService._write_dataframe_to_sheet(ws, data['horas_pico'], header_font, header_fill, border)

        if 'horas_pico_dia' in data and not data['horas_pico_dia'].empty:
            ws = wb.create_sheet('Horas Pico por Día')
            ReportService._write_dataframe_to_sheet(ws, data['horas_pico_dia'], header_font, header_fill, border)

        wb.save(output)
        output.seek(0)
        return output

    @staticmethod
    def _write_dataframe_to_sheet(ws, df, header_font, header_fill, border, include_index=False):
        formatted_columns = [ReportService._format_header_text(col) for col in df.columns]
        df_formatted = df.copy()
        df_formatted.columns = formatted_columns
        
        for r_idx, row in enumerate(dataframe_to_rows(df_formatted, index=include_index, header=True), 1):
            for c_idx, value in enumerate(row, 1):
                cell = ws.cell(row=r_idx, column=c_idx, value=value)
                cell.border = border
                if r_idx == 1:  # Header row
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal='center', vertical='center')
        
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

    @staticmethod
    def _exportar_pdf(data, metadata, filtros):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=50, bottomMargin=50)
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#366092'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#366092'),
            spaceAfter=12
        )

        temp_image_paths = []

        try:
            elements.append(Paragraph("Reporte Estadístico de Atenciones", title_style))
            elements.append(Spacer(1, 0.1*inch))

            def format_date_display(dt):
                if dt is None:
                    return 'N/A'
                
                if isinstance(dt, str):
                    try:
                        if '.' in dt:
                            dt = dt.split('.')[0]
                        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                    except:
                        return dt
                
                if isinstance(dt, datetime):
                    if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
                        return dt.strftime('%Y-%m-%d')
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                
                return str(dt)

            fecha_inicio_str = format_date_display(metadata.get('fecha_inicio'))
            fecha_fin_str = format_date_display(metadata.get('fecha_fin'))
            
            # Agregar información del area
            area_id = metadata.get('area_id')
            if area_id:
                area = db.session.query(Area).filter_by(id_area=area_id).first()
                if area:
                    elements.append(Paragraph(f"Área: {area.name}", styles['Heading3']))
                    elements.append(Spacer(1, 0.1*inch))
            
            elements.append(Paragraph(f"Periodo: {fecha_inicio_str} - {fecha_fin_str}", styles['Normal']))
            elements.append(Spacer(1, 0.3*inch))

            # Resumen General
            if 'resumen_general' in data and data['resumen_general']:
                elements.append(Paragraph("Resumen General", heading_style))
                resumen = data['resumen_general']
                resumen_data = [
                    ['Métrica', 'Valor'],
                    ['Total de Atenciones', f"{resumen.get('total_atenciones', 0):,}"],
                    ['Atendidas', f"{resumen.get('finalizadas', 0):,}"],
                    ['Reasignadas', f"{resumen.get('reasignadas', 0):,}"],
                    ['Canceladas', f"{resumen.get('canceladas', 0):,}"],
                    ['Tiempo Promedio (min)', f"{resumen.get('tiempo_promedio_minutos', 0):.2f}"],
                    ['Usuarios Activos', f"{resumen.get('usuarios_activos', 0):,}"],
                    ['Trámites Distintos', f"{resumen.get('tramites_distintos', 0):,}"]
                ]
                table = Table(resumen_data, colWidths=[3*inch, 2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.3*inch))

                total_estados = sum([resumen.get('finalizadas',0), resumen.get('reasignadas',0), resumen.get('canceladas',0)])
                if total_estados > 0:
                    img_path = ReportService._crear_grafica_estados(resumen)
                    if img_path:
                        temp_image_paths.append(img_path)
                        elements.append(Paragraph("Distribución de Estados de Atenciones", heading_style))
                        img = RLImage(img_path, width=4.0*inch, height=3.5*inch)
                        elements.append(img)
                        elements.append(Spacer(1, 0.3*inch))

            # Estadísticas por Trámite
            if 'tramites' in data and not data['tramites'].empty:
                elements.append(PageBreak())
                elements.append(Paragraph("Estadísticas por Trámite", heading_style))
                
                df_tramites = data['tramites'][['nombre_tramite', 'total_atenciones', 'finalizadas', 
                                               'reasignadas', 'canceladas', 'tiempo_promedio_minutos']].head(10).copy()
                df_tramites['nombre_tramite'] = df_tramites['nombre_tramite'].astype(str).apply(
                    lambda x: (x[:35] + '...') if len(x) > 35 else x
                )
                
                columnas_formateadas = [ReportService._format_header_text(col) for col in df_tramites.columns]
                table_data = [columnas_formateadas] + df_tramites.values.tolist()
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.3*inch))
                
                if df_tramites['total_atenciones'].sum() > 0:
                    img_path = ReportService._crear_grafica_top_tramites(data['tramites'])
                    if img_path:
                        temp_image_paths.append(img_path)
                        elements.append(Paragraph("Trámites con Mayor Demanda", heading_style))
                        img = RLImage(img_path, width=5.0*inch, height=3.5*inch)
                        elements.append(img)
                        elements.append(Spacer(1, 0.3*inch))

            # Estadísticas por Empleado
            if 'usuarios' in data and not data['usuarios'].empty:
                elements.append(PageBreak())
                elements.append(Paragraph("Estadísticas por Empleado", heading_style))
                
                df_usuarios = data['usuarios'][['nombre_completo', 'total_atenciones', 'finalizadas',
                                               'reasignadas', 'canceladas', 'tiempo_promedio_minutos']].head(10).copy()
                df_usuarios['nombre_completo'] = df_usuarios['nombre_completo'].astype(str).apply(
                    lambda x: (x[:30] + '...') if len(x) > 30 else x
                )
                
                columnas_formateadas = [ReportService._format_header_text(col) for col in df_usuarios.columns]
                table_data = [columnas_formateadas] + df_usuarios.values.tolist()
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.3*inch))
                
                if df_usuarios['total_atenciones'].sum() > 0:
                    img_path = ReportService._crear_grafica_top_empleados(data['usuarios'])
                    if img_path:
                        temp_image_paths.append(img_path)
                        elements.append(Paragraph("Empleados con Mayor Productividad", heading_style))
                        img = RLImage(img_path, width=5.0*inch, height=3.5*inch)
                        elements.append(img)
                        elements.append(Spacer(1, 0.3*inch))

            # Desglose por Empleado
            if 'usuarios' in data and not data['usuarios'].empty:
                tramites_por_emp = ReportService._tramites_por_empleado(filtros)
                if tramites_por_emp:
                    elements.append(PageBreak())
                    elements.append(Paragraph("Desglose de Trámites por Empleado", heading_style))
                    
                    for empleado, df_emp in tramites_por_emp.items():
                        emp_display = (empleado[:40] + '...') if len(empleado) > 40 else empleado
                        elements.append(Paragraph(f"Empleado: {emp_display}", styles['Heading3']))
                        
                        df_emp_limited = df_emp.head(10).copy()
                        table_data = [[ReportService._format_header_text('Trámite'), ReportService._format_header_text('Atenciones')]]
                        for _, row in df_emp_limited.iterrows():
                            tramite_text = Paragraph(row['tramite'], styles['Normal'])
                            table_data.append([tramite_text, row['total']])
                        
                        table = Table(table_data, colWidths=[4*inch, 1.5*inch])
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 9),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ]))
                        elements.append(table)
                        elements.append(Spacer(1, 0.2*inch))

            # Horas Pico
            if 'horas_pico' in data and not data['horas_pico'].empty and data['horas_pico']['total'].sum() > 0:
                elements.append(PageBreak())
                elements.append(Paragraph("Distribución de Atenciones por Hora", heading_style))
                img_path = ReportService._crear_grafica_horas_pico(data['horas_pico'])
                if img_path:
                    temp_image_paths.append(img_path)
                    img = RLImage(img_path, width=5.5*inch, height=3.0*inch)
                    elements.append(img)
                    elements.append(Spacer(1, 0.3*inch))

            # Patrón Semanal
            if 'horas_pico_dia' in data and not data['horas_pico_dia'].empty and data['horas_pico_dia']['total'].sum() > 0:
                elements.append(PageBreak())
                elements.append(Paragraph("Patrón Semanal de Atenciones", heading_style))
                img_path = ReportService._crear_heatmap_horas_dia(data['horas_pico_dia'])
                if img_path:
                    temp_image_paths.append(img_path)
                    img = RLImage(img_path, width=5.5*inch, height=3.5*inch)
                    elements.append(img)

            doc.build(elements)

        finally:
            for path in temp_image_paths:
                try:
                    os.unlink(path)
                except Exception as e:
                    print(f"Advertencia: No se pudo eliminar archivo temporal {path}: {e}")

        buffer.seek(0)
        return buffer

    @staticmethod
    def _crear_grafica_estados(resumen):
        try:
            estados = ['Atendidas', 'Reasignadas', 'Canceladas']
            valores = [
                resumen.get('finalizadas', 0),
                resumen.get('reasignadas', 0),
                resumen.get('canceladas', 0)
            ]
            if sum(valores) == 0:
                return None
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                fig, ax = plt.subplots(figsize=(6, 6))
                colors_pie = ['#2ecc71', '#f39c12', '#e74c3c']
                ax.pie(valores, labels=estados, autopct='%1.1f%%', startangle=90, colors=colors_pie)
                ax.set_title('Distribución de Estados de Atenciones', fontsize=12, fontweight='bold', pad=20)
                plt.tight_layout(pad=2.0)
                plt.savefig(tmp.name, dpi=150, bbox_inches='tight')
                plt.close()
                return tmp.name
        except Exception as e:
            print(f"Error creando gráfica de estados: {e}")
            return None

    @staticmethod
    def _crear_grafica_top_tramites(df):
        try:
            if df.empty or df['total_atenciones'].sum() == 0:
                return None
            df_sorted = df.nlargest(10, 'total_atenciones').copy()
            df_sorted['nombre_tramite'] = df_sorted['nombre_tramite'].astype(str).apply(
                lambda x: (x[:55] + '...') if len(x) > 55 else x
            )
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                fig, ax = plt.subplots(figsize=(7, 5))
                bars = ax.barh(df_sorted['nombre_tramite'], df_sorted['total_atenciones'], color='#3498db')
                ax.set_xlabel('Total de Atenciones', fontsize=10)
                ax.set_title('Trámites con Mayor Demanda', fontsize=12, fontweight='bold', pad=15)
                ax.invert_yaxis()
                ax.tick_params(axis='y', labelsize=8)
                ax.set_xlim(0, df_sorted['total_atenciones'].max() * 1.1)
                for bar in bars:
                    width = bar.get_width()
                    ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, str(int(width)),
                            va='center', ha='left', fontsize=8)
                plt.tight_layout(pad=2.0)
                plt.savefig(tmp.name, dpi=150, bbox_inches='tight')
                plt.close()
                return tmp.name
        except Exception as e:
            print(f"Error creando gráfica de trámites: {e}")
            return None

    @staticmethod
    def _crear_grafica_top_empleados(df):
        try:
            if df.empty or df['total_atenciones'].sum() == 0:
                return None
            df_sorted = df.nlargest(10, 'total_atenciones').copy()
            df_sorted['nombre_completo'] = df_sorted['nombre_completo'].astype(str).apply(
                lambda x: (x[:35] + '...') if len(x) > 35 else x
            )
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                fig, ax = plt.subplots(figsize=(7, 5))
                bars = ax.barh(df_sorted['nombre_completo'], df_sorted['total_atenciones'], color='#9b59b6')
                ax.set_xlabel('Total de Atenciones', fontsize=10)
                ax.set_title('Empleados con Mayor Productividad', fontsize=12, fontweight='bold', pad=15)
                ax.invert_yaxis()
                ax.tick_params(axis='y', labelsize=8)
                ax.set_xlim(0, df_sorted['total_atenciones'].max() * 1.1)
                for bar in bars:
                    width = bar.get_width()
                    ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, str(int(width)),
                            va='center', ha='left', fontsize=8)
                plt.tight_layout(pad=2.0)
                plt.savefig(tmp.name, dpi=150, bbox_inches='tight')
                plt.close()
                return tmp.name
        except Exception as e:
            print(f"Error creando gráfica de empleados: {e}")
            return None

    @staticmethod
    def _crear_grafica_horas_pico(df):
        try:
            if df.empty or df['total'].sum() == 0:
                return None
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.plot(df['hora'], df['total'], marker='o', linewidth=2, markersize=5, color='#e74c3c')
                ax.fill_between(df['hora'], df['total'], alpha=0.2, color='#e74c3c')
                ax.set_xlabel('Hora del Día', fontsize=10)
                ax.set_ylabel('Número de Atenciones', fontsize=10)
                ax.set_title('Distribución de Atenciones por Hora', fontsize=12, fontweight='bold', pad=15)
                ax.grid(True, alpha=0.3)
                min_hora = df['hora'].min()
                max_hora = df['hora'].max()
                ax.set_xlim(max(0, min_hora - 1), min(23, max_hora + 1))
                ax.set_xticks(range(int(min_hora), int(max_hora) + 1))
                ax.tick_params(axis='x', labelsize=8)
                ax.tick_params(axis='y', labelsize=8)
                plt.tight_layout(pad=2.0)
                plt.savefig(tmp.name, dpi=150, bbox_inches='tight')
                plt.close()
                return tmp.name
        except Exception as e:
            print(f"Error creando gráfica de horas pico: {e}")
            return None

    @staticmethod
    def _crear_heatmap_horas_dia(df):
        try:
            if df.empty or df['total'].sum() == 0:
                return None
            pivot_data = df.pivot_table(values='total', index='hora', columns='dia_nombre', fill_value=0)
            dias_orden = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            pivot_data = pivot_data.reindex(columns=[d for d in dias_orden if d in pivot_data.columns], fill_value=0)
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                fig, ax = plt.subplots(figsize=(8, 5))
                sns.heatmap(pivot_data, annot=True, fmt='g', cmap='YlOrRd', ax=ax,
                            cbar_kws={'label': 'Atenciones'}, annot_kws={"size": 8})
                ax.set_xlabel('Día de la Semana', fontsize=10)
                ax.set_ylabel('Hora del Día', fontsize=10)
                ax.set_title('Patrón Semanal de Atenciones', fontsize=12, fontweight='bold', pad=15)
                ax.tick_params(axis='x', labelsize=8, rotation=30)
                ax.tick_params(axis='y', labelsize=8)
                plt.tight_layout(pad=2.0)
                plt.savefig(tmp.name, dpi=150, bbox_inches='tight')
                plt.close()
                return tmp.name
        except Exception as e:
            print(f"Error creando heatmap: {e}")
            return None