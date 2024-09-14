FROM debian:12
MAINTAINER "Holger Lamm <holger_lamm@web.de>"
COPY dcpomatic-cli_2.16.91-1_amd64.deb /tmp
RUN apt-get update && dpkg -i /tmp/dcpomatic-cli_2.16.91-1_amd64.deb || true
RUN apt install -f -y
WORKDIR /data
CMD /bin/bash

