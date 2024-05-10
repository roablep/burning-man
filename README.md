# rivanna-py

## Repo Setup
### Install Python3.11
```
conda create --name burning-man 6 python=3.11.6
```
Then activate it
```
conda activate burning-man
```

### Create a virtual env and activate it
```
python3 -m venv .venv
```
```
source activate.sh
```


## Setup your local envirorment for development

```
source build-dev.sh
```

## Running the Streamlit server
`streamlit run src/bm/bm_streamlit_app.py`