"""PDF/Excel report generation, graphical reports, and the JSON API that feeds the charts."""

from io import BytesIO

import pandas as pd
from flask import Blueprint, render_template, request, session, jsonify, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

from app.extensions import db
from app.utils.decorators import login_required
from app.utils.currency import get_exchange_rates

reports_bp = Blueprint("reports", __name__)


def _user_expenses(user_id):
    return db.execute(
        """
        SELECT title, amount, date, category FROM expenses WHERE user_id = ?
        UNION ALL
        SELECT title, amount, start_date AS date, category FROM recurring_expenses WHERE user_id = ?
        ORDER BY date DESC
        """,
        user_id, user_id,
    )


@reports_bp.route("/generate_report", methods=["GET", "POST"])
@login_required
def generate_report():
    user_id = session["user_id"]
    user = db.execute("SELECT username FROM users WHERE id = ?", user_id)[0]
    expenses = _user_expenses(user_id)

    if request.method == "POST":
        report_type = request.form.get("report_type")
        report_currency = request.form.get("report_currency", "USD")

        rates = get_exchange_rates("USD")
        rate = rates.get(report_currency, 1)

        converted_expenses = []
        for expense in expenses:
            converted_expenses.append({
                **expense, "converted_amount": round(expense["amount"] * rate, 2)
            })

        if report_type == "pdf":
            return _build_pdf_report(user["username"], report_currency, converted_expenses)
        if report_type == "excel":
            return _build_excel_report(converted_expenses)

    return render_template("generate_report.html", has_expenses=bool(expenses))


def _build_pdf_report(username, report_currency, converted_expenses):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Title"], spaceAfter=14)
    elements.append(Paragraph("FinTrack Expense Report", title_style))

    subtitle_style = ParagraphStyle("Normal", parent=styles["Normal"], spaceAfter=14)
    elements.append(Paragraph(f"Username: {username}", subtitle_style))
    elements.append(Paragraph(f"Report Currency: {report_currency}", subtitle_style))

    if converted_expenses:
        data = [["ID", "Title", "Amount (USD)", f"Amount ({report_currency})", "Date", "Category"]]
        for idx, expense in enumerate(converted_expenses, start=1):
            data.append([
                idx, expense["title"], f"${expense['amount']:.2f}",
                f"{expense['converted_amount']:.2f} {report_currency}", expense["date"], expense["category"],
            ])

        table = Table(data, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F3F4F6")),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#D1D5DB")),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No expenses found.", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="expense_report.pdf", mimetype="application/pdf")


def _build_excel_report(converted_expenses):
    data_frame = pd.DataFrame(converted_expenses)
    if not data_frame.empty:
        data_frame.insert(0, "ID", range(1, 1 + len(data_frame)))
    buffer = BytesIO()
    data_frame.to_excel(buffer, index=False)
    buffer.seek(0)
    return send_file(
        buffer, as_attachment=True, download_name="expense_report.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@reports_bp.route("/generate_graphical_report")
@login_required
def generate_graphical_report():
    return render_template("graphical_reports.html")


@reports_bp.route("/expense_data")
@login_required
def expense_data():
    """JSON feed consumed by Chart.js on the graphical reports page."""
    user_id = session["user_id"]
    expenses = db.execute(
        """
        SELECT date, amount, category FROM expenses WHERE user_id = ?
        UNION ALL
        SELECT start_date AS date, amount, category FROM recurring_expenses WHERE user_id = ?
        """,
        user_id, user_id,
    )
    return jsonify(expenses)
