# time off form

Automate the filling of time off request forms


## dev

```bash
poetry install



poetry run python -m timeoff.pdf_generation \
    --input-path form.pdf \
    --employee-name 'Christopher Dignam' \
    --employee-signature '~~Chris' \
    --employee-requested-dates '2019-08-16 to 2019-08-20'

poetry run python -m timeoff.web
```
