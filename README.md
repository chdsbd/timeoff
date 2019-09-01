# time off form

Automate the filling of time off request forms


## dev

```
poetry install



poetry run python main.py  --input-path form.pdf \
    --employee-name 'Christopher Dignam' \
    --employee-signature '~~Chris' \
    --employee-requested-dates '2019-08-16 to 2019-08-20' \
    --manager-name 'Brad' \
    --manager-signature '~~Brad'
```
