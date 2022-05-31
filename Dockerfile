FROM python:2.7.14-jessie AS build

COPY . /src

RUN pip install --upgrade pip && pip install wheel
RUN cd /src && python setup.py bdist_wheel -d /deps


FROM python:2.7.14-jessie

COPY --from=build /deps/* /deps/
COPY requirements.txt production.ini /app/

RUN apt-get update && \
    apt-get install python-lxml
RUN pip install --upgrade pip && pip install waitress
RUN pip install --no-cache-dir -r /app/requirements.txt && \
    pip install --no-index --find-links=file:///deps -U booksoai
RUN rm -rf /deps

WORKDIR /app

USER nobody
EXPOSE 6543

CMD gunicorn --paste /app/production.ini
