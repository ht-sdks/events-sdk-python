PWD := $(shell pwd)
BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

build:
	docker build -t events-sdk-python/${BRANCH} .

clean:
	docker rmi events-sdk-python/${BRANCH}

repl:
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} python

pylint:
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} \
	pylint --rcfile=.pylintrc --reports=y --exit-zero segment/analytics | tee pylint.out

black:
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} \
	python -m black segment/analytics

flake8:
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} \
	flake8 --max-complexity=10 --statistics segment/analytics > flake8.out || true

test:
	docker run --rm -it -v ${PWD}:/dkr events-sdk-python/${BRANCH} \
	python -m unittest segment.analytics.test.all

release:
	python setup.py sdist bdist_wheel
	twine upload dist/*

e2e_test:
	.buildscripts/e2e.sh

.PHONY: build clean repl pylint flake8 black test release e2e_test
