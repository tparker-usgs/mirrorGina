# mirror files from GINA
#
# BUILD-USING:        docker build -t mirrorgina .
# RUN-USING docker run --detach=true --volumes-from data --name mirrorgina mirrorgina
#

# can't use onbuild due to SSL visibility
FROM python:2.7

RUN apt-get update && apt-get -y install cron

WORKDIR /root/.pip
ADD pip.conf .

WORKDIR /root/certs
add DOIRootCA2.cer .

WORKDIR /usr/share/ca-certificates/extra
add DOIRootCA2.cer DOIRootCA2.crt
RUN echo "extra/DOIRootCA2.crt" >> /etc/ca-certificates.conf && update-ca-certificates

WORKDIR /app/mirrorGina
ADD requirements.txt .
ADD single.py .
ADD mirror_gina.py .
ADD cron-mirrorGina /etc/cron.d/
RUN pip install --no-cache-dir -r requirements.txt

CMD ["cron","-f"]
