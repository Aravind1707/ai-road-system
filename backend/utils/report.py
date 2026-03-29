from fpdf import FPDF
from datetime import datetime


def generate_complaint_pdf(complaint_data: dict, file_path: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(190, 10, 'Road Damage Complaint Report', ln=1, align='C')

    pdf.set_font('Arial', '', 12)
    for key, value in complaint_data.items():
        pdf.cell(0, 8, f'{key}: {value}', ln=True)

    pdf.cell(0, 8, f'Report generated: {datetime.utcnow().isoformat()}', ln=True)
    pdf.output(file_path)
    return file_path
