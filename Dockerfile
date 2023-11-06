FROM python:3.11

# TODO: fix pylint with 3.11 (3.7, 3.8, 3.9, 3.10 work)

WORKDIR /dkr
COPY . /dkr

RUN python -m pip install --upgrade pip
RUN python -m pip install -e .[test]

# TODO: rename as requirements_frozen_for_documentation.txt
# these don't actually need to be frozen to these reqs...
# RUN python -m pip install -r requirements.txt

CMD python
