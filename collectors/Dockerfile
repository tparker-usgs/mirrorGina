# mirror files from GINA
#
# BUILD-USING:  docker build -t mirrorgina .
# RUN-USING:    docker run --detach=true --volumes-from data --name mirrorgina mirrorgina
#

# can't use onbuild due to SSL visibility
FROM python:2.7

RUN apt-get update && apt-get -y install cron libhdf5-serial-dev

WORKDIR /root/.pip
ADD pip.conf .

WORKDIR /root/certs
add DOIRootCA2.cer .

WORKDIR /usr/share/ca-certificates/extra
ADD DOIRootCA2.cer DOIRootCA2.crt
RUN echo "extra/DOIRootCA2.crt" >> /etc/ca-certificates.conf && update-ca-certificates

WORKDIR /app/collectors
ADD requirements.txt .
RUN pip install --default-timeout=60 --no-cache-dir -r requirements.txt # 1

ADD bin bin
# 1
ADD viirs viirs
ADD cron-collectors /tmp/cron-collectors
ADD run_crond.sh  .
RUN chmod 755 run_crond.sh

#CMD ["cron","-f"]
CMD ["/app/collectors/run_crond.sh"]
