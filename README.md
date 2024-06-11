# avmpi_scripts

![Tests](https://github.com/brnco/avmpi_scripts/actions/workflows/tests.yml/badge.svg?branch=dev)

The home of the Smithsonian Library and Archives Audiovisual Media Preservation Initiative's software automations

# Installation

1. Clone the repo to anywhere on your machine

--I suggest `/home/your_username/code/` as the parent directory, so the local path to this repo would be `/home/your_username/code/avmpi_scripts`

2. Set up Virtual Environment

In order to protect your system's version of Python and any various packages it utilizes, we need to create our own separate Python environment in this repo.

To do this, we use the [venv module](https://docs.python.org/3/library/venv.html)

Navigate to the top level directory of this repo and run the following command

`python -m venv venv`

3. Start the Virtual Environment

Now that we have our virtual environment initialized, we need to run it so that we can install our dependencies and run the scripts.

To do that on Mac, run

`source venv/bin/activate`

4. Install dependencies

All of the dependencies are detailed in `requirements.txt`. To install them, use

`python -m pip -r requirements.txt`

This will take a minute, you'll see a lot of text onscreen.

You should now be all set to run the scripts!

## Troubleshooting

If you get a `ModuleNotFoundError` or `ImportError` when you run a script, you can install the offending module to the `venv` using

`python -m pip install [module_name]`

# Airtable configuration

In order to integrate Airtable and Python, we need to link your Airtable account with the script. This is done through the use of a [Personal Access Token (PAT)](https://airtable.com/developers/web/guides/personal-access-tokens).

## Create a Personal Access Token

Follow the official documentation [at this link](https://airtable.com/developers/web/guides/personal-access-tokens#creating-a-token).

For Scopes, use:

```
data.records:read
See the data in records

data.records:write
Create, edit, and delete records

schema.bases:read
See the structure of a base, like table names or field types
```

For Access, we only need access to the `Assets` base

