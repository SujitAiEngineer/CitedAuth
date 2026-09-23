"""
Pure layout: takes already-decided text and lays it into a PDF. No model
calls happen here -- that's summarize_reason's job -- so a PDF always
renders even if the prose call upstream fell back to the raw reason.
"""
from datetime import date

from fpdf import FPDF

from backend.app.models import DeterminationResult


def _add_letter_page(pdf: FPDF, result: DeterminationResult, letter_text: str) -> None:
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Prior Authorization Determination", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Date: {date.today().isoformat()}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.cell(0, 8, f"To: {result.requesting_provider}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(
        0, 8,
        f"Re: Member {result.member_id} - {result.procedure} (Request #{result.request_id})",
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Determination: {result.determination.upper()}", new_x="LMARGIN", new_y="NEXT")
    if result.policy_id:
        pdf.set_font("Helvetica", "", 10)
        cite = f"Policy: {result.policy_id}"
        if result.criterion:
            cite += f", criterion {result.criterion}"
        pdf.cell(0, 7, cite, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 7, letter_text)
    pdf.ln(12)

    pdf.cell(0, 8, "Sincerely,", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Nurse on Duty", new_x="LMARGIN", new_y="NEXT")


def build_letters_pdf(items: list[tuple[DeterminationResult, str]]) -> bytes:
    """One PDF, one page per (result, letter_text) pair, in the order given."""
    pdf = FPDF()
    for result, letter_text in items:
        _add_letter_page(pdf, result, letter_text)
    return bytes(pdf.output())
