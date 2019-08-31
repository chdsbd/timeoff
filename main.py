import os

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
@click.option("--output-path", type=click.Path(), required=True)
@click.option("--employee-name", required=True)
@click.option("--employee-signature", required=True)
@click.option("--employee-requested-dates", required=True)
@click.option("--manager-name", required=True)
@click.option("--manager-signature", required=True)
def write_fillable_pdf(
    input_path,
    output_path,
    employee_name,
    employee_signature,
    employee_requested_dates,
    manager_name,
    manager_signature,
):
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
    click.launch(output_path, locate=True)


if __name__ == "__main__":
    write_fillable_pdf()
