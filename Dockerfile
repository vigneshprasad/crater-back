FROM python:3.9-slim-buster

ENV PYTHONUNBUFFERED 1
EXPOSE 8000 8000

# Add system/runtime requirements, awscli
RUN apt-get update \
	&& apt-get install -y -f --no-install-recommends jq gettext curl git unzip binutils gdal-bin postgresql-client gcc musl-dev libxslt-dev libffi-dev gnupg npm \
	&& curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"\
	&& unzip awscliv2.zip \
	&& ./aws/install -i /usr/local/aws-cli -b /usr/local/bin \
	&& rm -rf awscliv2.zip ./aws \
	&& npm install -g aws-cdk@2.14.0


# Add Docker, Kubetctl
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
	&& echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
  buster stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
  	&& apt-get update  \
	&& apt-get install -y docker-ce docker-ce-cli containerd.io \
	&& rm -rf /var/lib/apt/lists/*



COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip-tools \
	&& pip-sync requirements.txt
RUN rm -f requirements.txt

RUN mkdir /app
COPY . /app/
WORKDIR /app/

