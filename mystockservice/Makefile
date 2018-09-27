# Some simple testing tasks (sorry, UNIX only).

FLAGS=


flake:
	flake8 lucky setup.py

clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -f `find . -type f -name '@*' `
	rm -f `find . -type f -name '#*#' `
	rm -f `find . -type f -name '*.orig' `
	rm -f `find . -type f -name '*.rej' `
	rm -f .coverage
	rm -rf coverage
	rm -rf build
	rm -rf htmlcov
	rm -rf dist

run:
	pipenv run python -m lucky

sync_k:
	pipenv run python lucky/commands/sync_k_files.py

volume:
	python lucky/commands/volume.py

fake_data:
	python ./lucky/generate_data.py

# docker_start_mongo:
# 	docker-compose -f docker-compose.yml up -d mongo

# docker_stop_mogo:
# 	docker-compose -f docker-compose.yml stop mongo

.PHONY: flake clean
