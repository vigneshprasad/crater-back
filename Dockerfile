ARG builder_image=builder
ARG runner_image=runner

FROM python:3.8-slim-buster as builder
ARG requirements_file=requirements.txt
COPY $requirements_file ./
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN apt-get update && apt-get install gcc zlib1g-dev libjpeg-dev -y && pip install --upgrade pip && pip install -r $requirements_file

FROM python:3.8-slim-buster as runner
RUN apt-get update && apt-get install software-properties-common -y && apt-get install python3-dev gdal-bin libgdal-dev -y

FROM $builder_image as final_builder
FROM $runner_image as final
COPY --from=final_builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY / ./
CMD ["./bin/entry_point.sh"]