FROM python:3.12.7-slim

ENV PROJECT_ROOT=/workspace
WORKDIR $PROJECT_ROOT

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install poetry.
ENV POETRY_HOME=/root/.poetry
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 - && poetry config virtualenvs.create false;

# Copy in the dependency files for caching.
COPY pyproject.toml poetry.lock ./

# Install the dependencies only to utilise layer caching for quick rebuilds.
RUN poetry install  \
    --no-ansi  \
    --no-interaction  \
    --no-cache  \
    --no-root  \
    --only main

# Copy local code to the application root directory.
COPY . .

RUN poetry install --only main

ENTRYPOINT ["publish-strand-version"]
