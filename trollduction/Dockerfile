# mirror files from GINA
#
# BUILD-USING:	docker build -t rsprocessing .
# RUN-USING:	docker run --detach=true --volumes-from data --name rsprocessing rsprocessing
#

# can't use onbuild due to SSL visibility
FROM python:2.7

RUN apt-get update && apt-get -y install libhdf5-serial-dev libnetcdf-dev less unzip libfreetype6 libfreetype6-dev 
#python-numpy python-scipy python-matplotlib libhdf5-serial-dev libnetcdf-dev

RUN ln -s /usr/include/freetype2 /usr/include/freetype  

RUN wget http://download.osgeo.org/gdal/CURRENT/gdal-2.1.1.tar.gz \
	&& (gzip -dc gdal-2.1.1.tar.gz | tar xf -) \
	&& cd gdal-2.1.1 \
	&& ./configure; make; make install \
	&& ldconfig \
	&& cd .. && rm -rf gdal-2.1.1 gdal-2.1.1.tar.gz

WORKDIR /root/.pip
ADD pip.conf .

WORKDIR /root/certs
ADD DOIRootCA2.cer .

WORKDIR /usr/share/ca-certificates/extra
ADD DOIRootCA2.cer DOIRootCA2.crt
RUN echo "extra/DOIRootCA2.crt" >> /etc/ca-certificates.conf && update-ca-certificates

WORKDIR /src

WORKDIR /src/app
ADD requirements.txt /src/app/
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app/gshhg
RUN wget http://www.ngdc.noaa.gov/mgg/shorelines/data/gshhg/latest/gshhg-shp-2.3.5-1.zip \
	&& unzip gshhg-shp-2.3.5-1.zip && rm gshhg-shp-2.3.5-1.zip

#ADD http://effbot.org/media/downloads/aggdraw-1.1-20051010.zip .
#RUN export CFLAGS="-fpermissive" && unzip  aggdraw-1.1-20051010.zip && \
#        cd aggdraw-1.1-20051010 && python setup.py install

RUN export CFLAGS="-fpermissive" && git clone git://github.com/tparker-usgs/aggdraw.git && \
	cd aggdraw && python setup.py install && cd .. && rm -r aggdraw

# update pytroll
WORKDIR /usr/src/
ADD installPytroll.sh .
RUN ./installPytroll.sh && cd .. && rm -r /usr/src

COPY trollConfig /app/trollConfig
COPY supervisord.conf /usr/local/etc/supervisord.conf

CMD ["/usr/local/bin/supervisord"]
