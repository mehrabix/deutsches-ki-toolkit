# PostgreSQL mit pgvector.
#
# Normalerweise genügt das fertige Image `pgvector/pgvector:pg17`. Wo Docker Hub
# nicht erreichbar ist, lässt sich das Image stattdessen selbst bauen:
#
#   docker build -f docker/postgres/Dockerfile -t deutsches-ki-postgres:17 .
#
# Die Basis lässt sich über `--build-arg BASE=...` austauschen.

ARG BASE=public.ecr.aws/docker/library/postgres:17
FROM ${BASE}

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-17-pgvector \
    && rm -rf /var/lib/apt/lists/*
