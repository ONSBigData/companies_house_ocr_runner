lint:
	black --check src/

test: lint
	python setup.py test

package: lint
	python setup.py test sdist bdist_wheel

install: package
	pip install --no-deps -e .

.PHONY: lint test package install
