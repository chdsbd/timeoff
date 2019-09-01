# time off

This bot isn't really useful for anyone besides employees at AdmitHub.

This bot is triggered by a slash command `/timeoff`, which opens a Slack dialog
to get data to fill into the PDF form. Some Python code fills in a PDF and
uploads it to the channel.


## dev

```bash
# install dependencies
poetry install

# copy environment file
cp .env-example .env

# create an app and copy the token in the .env file
open 'https://api.slack.com/apps?new_app=1'

# generate a pdf
poetry run python -m timeoff.pdf_generation \
    --input-path form.pdf \
    --employee-name 'Christopher Dignam' \
    --employee-signature '~~Chris' \
    --employee-requested-dates '2019-08-16 to 2019-08-20'

# start the slack bot web server
poetry run python -m timeoff.web
```

## deployment
Deployment uses zappa which is a wrapper around AWS Lambda. See the [Zappa
documentation](https://github.com/Miserlou/Zappa) for info on setting up an
environment.

When you first deploy you'll get a health check error because we need to
configure the environment variables for the lambda function to include the app
token.

```bash
# setup an environment for the first time
poetry run zappa deploy dev

# redeploy an environment
poetry run zappa update dev

# view logs
poetry run zappa tail dev
```
