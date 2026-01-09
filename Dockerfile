FROM python:3.12-alpine
LABEL manintainer="Konstantin-SVT"

WORKDIR app/

RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
RUN mkdir -p media
RUN mkdir -p fixtures

RUN adduser --no-create-home --disabled-password django-user
RUN chown -R django-user media
RUN chmod -R 755 media
USER django-user