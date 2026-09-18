# Image für die Kommandozeile `deutsches-ki`.
#
# Standardmäßig wird das offizielle Python-Image verwendet. Wo Docker Hub nicht
# erreichbar ist, lässt sich eine andere Registry wählen:
#
#   docker build -f docker/Dockerfile \
#     --build-arg BASE=public.ecr.aws/docker/library/python:3.12-slim \
#     -t deutsches-ki-toolkit .

ARG BASE=python:3.12-slim
FROM ${BASE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Nur die Grundinstallation. Die schweren Erweiterungen (spacy, presidio,
# docling, embeddings, postgres) kommen bei Bedarf dazu, damit das Image
# schlank bleibt.
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .

RUN useradd --create-home --uid 1000 toolkit
USER toolkit

WORKDIR /daten
ENTRYPOINT ["deutsches-ki"]
CMD ["--help"]
