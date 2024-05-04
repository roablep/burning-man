source .venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)

python -m pip install --upgrade pip
python -m pip install -e ".[dev,test]"