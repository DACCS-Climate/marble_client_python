
upgrade-build-packages:
	pip install --upgrade build
	pip install --upgrade twine

build: upgrade-build-packages
	python -m build

upload:
	twine upload dist/*

test-upload:
	twine upload --repository testpypi dist/*