FROM openjdk:8

ENV SCALA_LABRAD_WEB_VERSION=2.0.6

ENV PATH="/usr/local/scalabrad-web-server/bin:${PATH}"

COPY source/scalabrad-web-server-${SCALA_LABRAD_WEB_VERSION}.tar.gz scalabrad-web-server-${SCALA_LABRAD_WEB_VERSION}.tar.gz

RUN tar xvzf scalabrad-web-server-${SCALA_LABRAD_WEB_VERSION}.tar.gz &&\
  rm scalabrad-web-server-${SCALA_LABRAD_WEB_VERSION}.tar.gz &&\
  mv scalabrad-web-server-${SCALA_LABRAD_WEB_VERSION} /usr/local/scalabrad-web-server

EXPOSE 7667

CMD [ "labrad-web", "--host", "0.0.0.0" ]