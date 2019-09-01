import io
import json
import os
import tempfile
from pathlib import Path
from time import time
from typing import Optional
from uuid import uuid4

import click
import pdfrw
from pdfrw import PageMerge, PdfReader, PdfWriter
from reportlab.pdfgen import canvas

WIDGET_SUBTYPE_KEY = "/Widget"

# draw text into PDF
DRAW_TEXT = True
# fill in AcroForm fields. This works with Acrboat, macOS Preview, Chrome,
# PDFjs, but not Slack! So we need to draw the text instead.
USE_ACROFORM = False
PADDING = 4

# https://github.com/mozilla/pdf.js/issues/4244
def get_temp_pdf() -> str:
    _handle, path = tempfile.mkstemp(suffix=".pdf")
    return path


def draw_text_on_annotation(
    pdf: canvas.Canvas, annotation: pdfrw.PdfDict, text: str
) -> None:
    # canvas drawing modified from https://medium.com/@zwinny/filling-pdf-forms-in-python-the-right-way-eb9592e03dba
    sides_positions = annotation.Rect
    left = min(float(sides_positions[0]), float(sides_positions[2]))
    bottom = min(float(sides_positions[1]), float(sides_positions[3]))
    pdf.drawString(x=left + PADDING, y=bottom + PADDING, text=str(text))


def write_fillable_pdf(
    input_path: str,
    employee_name: Optional[str] = None,
    employee_signature: Optional[str] = None,
    employee_requested_dates: Optional[str] = None,
    manager_name: Optional[str] = None,
    manager_signature: Optional[str] = None,
    output_path: Optional[str] = None,
) -> str:
    # generate a random output path if we don't provide one
    if output_path is None:
        output_path = get_temp_pdf()
    template_pdf = pdfrw.PdfReader(input_path)

    if USE_ACROFORM:
        # Make filled form values visible immediately in Acrobat. This isn't required for macOS Preview.
        # https://github.com/pmaupin/pdfrw/issues/84#issuecomment-463493521
        template_pdf.Root.AcroForm.update(
            pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject("true"))
        )

    # data to fill into form. Mapping of PDF form labels to values.
    form_data = dict(
        employee_name=employee_name,
        employee_signature=employee_signature,
        requested_dates=employee_requested_dates,
        manager_name=manager_name,
        manager_approval=manager_signature,
    )

    # build a canvas to write text onto. We must draw the form values instead of
    # just using AcroForm filling because Slack uses PDFjs in a way that doesn't support fonts specified for fillable fields.
    # PDFjs renders the AcroForm filled fields fine, but Slack's version doesn't.
    #
    # The following errors log to console when viewing the PDF in Slack:
    #
    # ```
    # Warning: fontRes not available
    # Warning: Error during font loading: Font Cour is not available
    # ```
    d = io.BytesIO()
    temporary_pdf_name = get_temp_pdf()
    pdf = canvas.Canvas(temporary_pdf_name)

    first_page = annotations = template_pdf.pages[0]
    # AcroForm filling modified from https://bostata.com/how-to-populate-fillable-pdfs-with-python/
    for annotation in first_page.Annots:
        if annotation.Subtype != WIDGET_SUBTYPE_KEY:
            continue
        # check if the annotation has a field key
        if not annotation.T:
            continue
        # remove the parenthesis from the label name.
        # "(first_name)" => "first_name"
        field_label = annotation.T[1:-1]
        if field_label not in form_data.keys():
            continue
        value = form_data[field_label]
        # leave the field untouched if a value isn't provided.
        if not value:
            continue
        if DRAW_TEXT:
            draw_text_on_annotation(pdf, annotation, text=str(value))
        patch = pdfrw.PdfDict()
        if USE_ACROFORM:
            patch.V = str(value)
        # mark field as ReadOnly
        patch.Ff = 1
        annotation.update(patch)

    pdf.showPage()
    pdf.save()
    # modified from https://github.com/pmaupin/pdfrw/blob/6c892160e7e976b243db0c12c3e56ed8c78afc5a/examples/watermark.py
    drawn_text_pdf = PageMerge().add(PdfReader(temporary_pdf_name).pages[0])[0]
    page = template_pdf.pages[0]
    PageMerge(page).add(drawn_text_pdf).render()
    pdfrw.PdfWriter().write(output_path, template_pdf)
    # remove temporary file
    os.remove(temporary_pdf_name)
    return output_path


@click.command()
@click.option(
    "--input-path", type=click.Path(exists=True, dir_okay=False), required=True
)
@click.option("--output-path", type=click.Path())
@click.option("--employee-name")
@click.option("--employee-signature")
@click.option("--employee-requested-dates")
@click.option("--manager-name")
@click.option("--manager-signature")
def write_fillable_pdf_cli(
    input_path: str,
    output_path: Optional[str] = None,
    employee_name: Optional[str] = None,
    employee_signature: Optional[str] = None,
    employee_requested_dates: Optional[str] = None,
    manager_name: Optional[str] = None,
    manager_signature: Optional[str] = None,
) -> None:
    output_path = write_fillable_pdf(
        input_path,
        output_path,
        employee_name,
        employee_signature,
        employee_requested_dates,
        manager_name,
        manager_signature,
    )
    click.echo(f"pdf written: {output_path}")
    click.launch(output_path, locate=True)


if __name__ == "__main__":
    write_fillable_pdf_cli()
