FROM openjdk:8

ENV SCALA_LABRAD_VERSION=0.8.3

ENV PATH="/usr/local/scalabrad/bin:${PATH}"

RUN wget --no-verbose \
  "https://github.com/labrad/scalabrad/releases/download/v${SCALA_LABRAD_VERSION}/scalabrad-${SCALA_LABRAD_VERSION}.tar.gz" &&\
  tar xvzf scalabrad-${SCALA_LABRAD_VERSION}.tar.gz &&\
  rm scalabrad-${SCALA_LABRAD_VERSION}.tar.gz &&\
  mv scalabrad-${SCALA_LABRAD_VERSION} /usr/local/scalabrad

EXPOSE 7682
EXPOSE 7643

CMD [ "labrad" ]