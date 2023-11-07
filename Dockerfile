FROM python:3.11

WORKDIR /dkr
COPY . /dkr

RUN python -m pip install --upgrade pip
RUN python -m pip install -e .[dev]

CMD python
