# kalufs-kepubify

Small flask application for converting epub into kepub.

## Requirements

* [Python 3.12](http://python.org/) or newer
* [uv](https://github.com/astral-sh/uv)
* [kepubify](https://pgaskin.net/kepubify/)

## Setup

1. Create an `instance` folder in the root of the project.
2. Download the [kepubify binary](https://pgaskin.net/kepubify/) and place it in the `instance` folder. Make sure it is
   executable (e.g. `chmod +x instance/kepubify`).
3. Copy `kepubify/config.py` to `instance/config.py` and edit the configuration as needed.
4. Install the dependencies with `uv sync`.
5. Run the application with `uv run run.py`.

## TODO

* Content type issue
* Add image?
