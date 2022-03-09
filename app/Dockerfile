ARG builder_image=builder
ARG runner_image=runner

FROM python:3.8-slim-buster as builder
COPY requirements.txt ./
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN apt-get update && apt-get install gcc python3-sklearn python3-sklearn-lib zlib1g-dev libjpeg-dev -y && pip install --upgrade pip && pip install -r requirements.txt

FROM python:3.8-slim-buster as runner
RUN apt-get update && apt-get install software-properties-common -y && apt-get install python3-dev gdal-bin libgdal-dev -y

FROM $builder_image as final_builder
FROM $runner_image as final
COPY --from=final_builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY / ./
CMD ["./bin/entry_point.sh"]
