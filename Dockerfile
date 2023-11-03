FROM python:3.10

# TODO: fix pylint with 3.11 (3.7, 3.8, 3.9, 3.10 work)

COPY . .

RUN python -m pip install --upgrade pip
RUN python -m pip install -e .[test]
RUN python -m pip install -r requirements.txt

CMD python
