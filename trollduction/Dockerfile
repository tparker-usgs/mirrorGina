# mirror files from GINA
#
# BUILD-USING:	docker build -t trollduction .
# RUN-USING:	docker run -e PYTHONUNBUFFERED=1 --detach=true --volumes-from data --name trollduction trollduction
#

# can't use onbuild due to SSL visibility
FROM python:2.7

RUN apt-get update && apt-get -y install libhdf5-serial-dev libnetcdf-dev less unzip libfreetype6 libfreetype6-dev 
#python-numpy python-scipy python-matplotlib libhdf5-serial-dev libnetcdf-dev

RUN ln -s /usr/include/freetype2 /usr/include/freetype  

RUN wget http://download.osgeo.org/gdal/2.2.0/gdal-2.2.0.tar.gz \
	&& (gzip -dc gdal-2.2.0.tar.gz | tar xf -) \
	&& cd gdal-2.2.0 \
	&& ./configure; make; make install \
	&& ldconfig \
	&& cd .. && rm -rf gdal-2.2.0 gdal-2.2.0.tar.gz

WORKDIR /root/.pip
ADD pip.conf .

WORKDIR /root/certs
ADD DOIRootCA2.cer .

WORKDIR /usr/share/ca-certificates/extra
ADD DOIRootCA2.cer DOIRootCA2.crt
RUN echo "extra/DOIRootCA2.crt" >> /etc/ca-certificates.conf && update-ca-certificates

WORKDIR /src

WORKDIR /src/app
# 1
ADD requirements.txt /src/app/
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app/gshhg
RUN wget http://www.soest.hawaii.edu/pwessel/gshhg/gshhg-shp-2.3.6.zip \
	&& unzip gshhg-shp-2.3.5-1.zip && rm gshhg-shp-2.3.5-1.zip

#ADD http://effbot.org/media/downloads/aggdraw-1.1-20051010.zip .
#RUN export CFLAGS="-fpermissive" && unzip  aggdraw-1.1-20051010.zip && \
#        cd aggdraw-1.1-20051010 && python setup.py install

RUN export CFLAGS="-fpermissive" && git clone git://github.com/tparker-usgs/aggdraw.git && \
	cd aggdraw && python setup.py install && cd .. && rm -r aggdraw

WORKDIR /usr/src/

# 3
ADD installPytroll.sh .
RUN ./installPytroll.sh && cd .. && rm -r /usr/src

# 6
ADD installPytroll-tweaked.sh .
RUN ./installPytroll-tweaked.sh && cd .. && rm -r /usr/src

COPY supervisord.conf /usr/local/etc/supervisord.conf

# 8
COPY app /app
WORKDIR /app

ENV PPP_CONFIG_DIR=/app/trollConfig HOME=/home/tscan PYTHONPATH=/app/compositors LOG_DIR=/data/logs

CMD ["/usr/local/bin/supervisord"]
