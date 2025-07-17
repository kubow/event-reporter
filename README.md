# event-reporter
Getting reports on intersting matter


## Library maintain

work in a virtual environment

```shell
python -m venv planetary  # init directory
source planetary/bin/activate  # activate environment
pip-compile --upgrade --strip-extras requirements.in # regenerate dependencies
pip install -r requirements.txt  # install dependencies
```