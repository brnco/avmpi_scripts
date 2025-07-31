# avmpi_scripts

The home of the Smithsonian Library and Archives Audiovisual Media Preservation Initiative's software automations

🚧 this repo is under construction 🚧

# Installation

## Clone the repo to anywhere on your machine

I suggest `/home/your_username/code/` as the parent directory, so the local path to this repo would be `/home/your_username/code/avmpi_scripts`

## Install uv

For the longest time, python was a great language with a horrible distribution environment. Managing python versions and their dependencies was a particular pain point. This seems to have been largely resolved by [the uv project](https://docs.astral.sh/uv/guides/install-python/). Gone are the days when you needed to set up a virtual environment to run your code. Now, we just use uv.

### on Mac

[use Homebrew to install uv](https://formulae.brew.sh/formula/uv): `brew install uv`

## Sync uv

We need to ensure that the configuration for the project is sync'd with your local machine and all the dependencies are installed.

To do this:

cd into the project folder: `cd /home/your_username/code/avmpi_scripts`

then, sync uv: `uv sync`

# Airtable configuration

In order to integrate Airtable and Python, we need to link your Airtable account with the script. This is done through the use of a [Personal Access Token (PAT)](https://airtable.com/developers/web/guides/personal-access-tokens).

## Create a Personal Access Token

Follow the official documentation [at this link](https://airtable.com/developers/web/guides/personal-access-tokens#creating-a-token).

For Name, use: `YourFirstName_avmpi_scripts`

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

## Add PAT to Airtable config

Now that you have a personal access token, we need to add it to the Airtable config so that our scripts can use it. Open `airtable_config.json` in your favorite text editor, find the `api_key` key, and paste your PAT between the quotation marks on the value side. It should look like: `"api_key": "pat1234",`
