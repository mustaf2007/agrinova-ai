from __future__ import annotations

import csv
import io
from datetime import date
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def _pdf_safe(value):
    """Keep standard PDF fonts from failing on unsupported Unicode characters."""
    return str(value).encode("cp1252", errors="replace").decode("cp1252")


def _rows(report):
    rows = [
        ("Report generated", report.get("report_date", date.today().isoformat())),
        ("Farm location", report.get("location", "Not available")),
        ("Location precision", report.get("location_precision", "Not specified")),
        ("Latitude", report.get("latitude", "Not available")),
        ("Longitude", report.get("longitude", "Not available")),
        ("Crop / plant", report.get("crop", "Not available")),
        ("Variety / cultivar", report.get("variety", "Not available")),
        ("Farm size (ha)", report.get("area_ha", "Not available")),
        ("Production season", report.get("season", "Not available")),
        ("Production system", report.get("production_system", "Not available")),
        ("Reported soil pH", report.get("soil_ph", "Not supplied")),
        ("Current temperature (°C)", report.get("current_temperature_c", "Not available")),
        ("Relative humidity (%)", report.get("relative_humidity_pct", "Not available")),
        ("7-day forecast rainfall (mm)", report.get("forecast_rainfall_7d_mm", "Not available")),
        ("Historical mean daily temperature (°C)", report.get("historical_mean_temperature_c", "Not available")),
        ("Historical accumulated precipitation (mm)", report.get("historical_precipitation_mm", "Not available")),
        ("Historical valid days", report.get("historical_valid_days", "Not available")),
        ("Historical period", report.get("historical_period", "Not available")),
        ("ECOCROP scientific name", report.get("ecocrop_scientific_name", "Not matched")),
        ("ECOCROP reference ID", report.get("ecocrop_record_id", "Not available")),
    ]
    rows.extend(report.get("ecocrop_indicators", []))
    return [(label, "Not available" if value is None else value) for label, value in rows]


def build_farm_report_csv(report):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Section", "Date", "Indicator", "Value", "Unit", "Source"])
    for label, value in _rows(report):
        writer.writerow(["Farm profile and evidence", "", label, value, "", "AgriNova AI / cited source in report"])
    for item in report.get("forecast_daily", []):
        writer.writerow([
            "7-day weather forecast", item.get("date", ""),
            "Maximum temperature", item.get("temp_max", ""), "°C", "Open-Meteo",
        ])
        writer.writerow([
            "7-day weather forecast", item.get("date", ""),
            "Minimum temperature", item.get("temp_min", ""), "°C", "Open-Meteo",
        ])
        writer.writerow([
            "7-day weather forecast", item.get("date", ""),
            "Precipitation", item.get("precipitation", ""), "mm/day", "Open-Meteo",
        ])
    for item in report.get("historical_daily", []):
        writer.writerow([
            "Historical daily climate", item.get("date", ""),
            "Mean temperature", item.get("temperature_c", ""), "°C", "NASA POWER",
        ])
        writer.writerow([
            "Historical daily climate", item.get("date", ""),
            "Corrected precipitation", item.get("precipitation_mm_day", ""), "mm/day", "NASA POWER",
        ])
    return output.getvalue().encode("utf-8-sig")


def build_farm_report_pdf(report):
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title="AgriNova AI - Global Farm Intelligence Report",
        author="AgriNova AI",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"], alignment=TA_CENTER,
        textColor=colors.HexColor("#176B4A"), fontSize=19, leading=23,
        spaceAfter=5 * mm,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle", parent=styles["Normal"], alignment=TA_CENTER,
        textColor=colors.HexColor("#52665B"), fontSize=9, leading=12,
        spaceAfter=8 * mm,
    )
    note_style = ParagraphStyle(
        "ReportNote", parent=styles["BodyText"], fontSize=8, leading=11,
        textColor=colors.HexColor("#52665B"), spaceBefore=5 * mm,
    )
    story = [
        Paragraph("AgriNova AI", title_style),
        Paragraph("Global Farm Intelligence Report", styles["Heading2"]),
        Paragraph("Generated: " + escape(_pdf_safe(report.get("report_date", date.today().isoformat()))), subtitle_style),
    ]
    data = [[Paragraph("<b>Indicator</b>", styles["BodyText"]), Paragraph("<b>Value</b>", styles["BodyText"])]]
    for label, value in _rows(report):
        data.append([
            Paragraph(escape(_pdf_safe(label)), styles["BodyText"]),
            Paragraph(escape(_pdf_safe(value)), styles["BodyText"]),
        ])
    table = Table(data, colWidths=[68 * mm, 102 * mm], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E3F1E8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#18352A")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D7E2DA")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAF8")]),
    ]))
    story.extend([
        table,
        Spacer(1, 7 * mm),
        Paragraph("<b>Sources and interpretation</b>", styles["Heading3"]),
        Paragraph(
            "Weather forecast: Open-Meteo. Historical climate: NASA POWER daily point data. "
            "Crop ecological indicators: FAO ECOCROP species-level reference where a species record was matched. "
            "Values are location- and source-dependent; historical gridded data are not farm weather-station measurements. "
            "ECOCROP values are expert-compiled species-level references, not cultivar-specific prescriptions. "
            "This report does not generate planting dates, fertilizer rates, irrigation schedules or yield estimates.",
            note_style,
        ),
        Paragraph(
            "Use local agricultural extension advice and verified farm measurements before making production or input decisions.",
            note_style,
        ),
    ])
    document.build(story)
    return buffer.getvalue()
