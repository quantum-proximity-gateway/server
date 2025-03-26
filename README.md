# Server

<details>
  <summary><strong>Table of Contents</strong></summary>

- [Method 1 - Docker](#method-1---docker)
  - [Requirements](#requirements)
  - [Usage](#usage)
- [Method 2 - Python](#method-2---python)
  - [Requirements](#requirements-1)
  - [Installation](#installation)
  - [Usage](#usage-1)
- [Misc.](#misc)
- [License](#license)

</details>

This server is already deployed, so the instructions below are just in case you want to run the server locally (or change the code yourself).

There are 2 ways of running this server locally:

1) Via **Docker** - the server will run locally, but you will not be able to change the code. This method is extremely easy, is unlikely to have failing dependency problems, and also runs much quicker since liboqs doesn't need to be re-compiled.

2) Via **Python** as a litestar application - the server will run locally and you will need to change the code.

## Method 1 - Docker

### Requirements

- Docker

### Usage

Firstly, ensure docker is running and active. Then, run the following command:

```bash
docker run -p 8000:8000 raghav2005/qpg-server
```

If it is easier, `make docker` can also be run instead of that command (it runs the same thing).

## Method 2 - Python

### Requirements

- Pipenv

### Installation

Navigate to the `backend/` directory.

Then, to install the dependencies, run:

```bash
pipenv install -r requirements.txt && pipenv install
```

### Usage

You can either run the server directly, without spawning a new shell for pipenv, or you can activate the environment and run the server.

For the first option, run the following command:

```bash
pipenv run python -m litestar run --host 0.0.0.0 --port 8000
```

For the second, run the following commands in order:

```bash
pipenv shell
litestar run --host 0.0.0.0 --port 8000
```

> NOTE: You can check if the server is running by trying to access `http://localhost:8000` in a browser. If you see {"status":"success"} on the screen, the server is running.

## Misc.

- Instead of using the commands listed above individually, you can run `make docker`, `make install`, or `make run` from the root directory of this repository to run the server.

## License

This project is licensed under the terms of the MIT license. Refer to [LICENSE](LICENSE) for more information.
