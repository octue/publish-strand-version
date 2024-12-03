# This base image was pushed on 3rd December 2024. The hash used is the index digest for the 3.12.7-slim tag. See https://hub.docker.com/layers/library/python/3.12.7-slim/images/sha256-1c44018d7eb40488f29e7c6ad4991d3200507e14dca71b94fe61011815e98155?context=explore
FROM python:3.12.7-slim@sha256:60d9996b6a8a3689d36db740b49f4327be3be09a21122bd02fb8895abb38b50d

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
