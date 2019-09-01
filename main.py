"""
Modified from https://bostata.com/how-to-populate-fillable-pdfs-with-python/
"""

import os
from typing import Optional
from pathlib import Path
from time import time

import click
import pdfrw

ANNOT_KEY = "/Annots"
ANNOT_FIELD_KEY = "/T"
ANNOT_VAL_KEY = "/V"
ANNOT_RECT_KEY = "/Rect"
SUBTYPE_KEY = "/Subtype"
WIDGET_SUBTYPE_KEY = "/Widget"


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
def write_fillable_pdf(
    input_path: str,
    output_path: Optional[str],
    employee_name: Optional[str],
    employee_signature: Optional[str],
    employee_requested_dates: Optional[str],
    manager_name: Optional[str],
    manager_signature: Optional[str],
):
    if output_path is None:
        path_in = Path(input_path)
        output_path = str(
            path_in.with_name(path_in.stem + "-" + str(time())).with_suffix(
                path_in.suffix
            )
        )
    template_pdf = pdfrw.PdfReader(input_path)
    data = dict(
        employee_name=employee_name,
        employee_signature=employee_signature,
        requested_dates=employee_requested_dates,
        manager_name=manager_name,
        manager_approval=manager_signature,
    )
    annotations = template_pdf.pages[0][ANNOT_KEY]
    for annotation in annotations:
        if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
            if annotation[ANNOT_FIELD_KEY]:
                key = annotation[ANNOT_FIELD_KEY][1:-1]
                if key in data.keys():
                    annotation.update(pdfrw.PdfDict(V="{}".format(data[key])))

    pdfrw.PdfWriter().write(output_path, template_pdf)
    click.echo(f"pdf written: {output_path}")
    click.launch(output_path, locate=True)


if __name__ == "__main__":
    write_fillable_pdf()
