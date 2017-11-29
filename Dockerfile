FROM debian:latest

MAINTAINER james.hn.sears@gmail.com

RUN apt-get -qq update
RUN apt-get -qq install -y openjdk-8-jre

ARG OPTDIR=/opt/
ARG XQA=xqa-shard

RUN mkdir ${OPTDIR}/${XQA}
COPY src ${OPTDIR}/${XQA}
ADD requirements.txt ${OPTDIR}/${XQA}

RUN apt-get -qq remove cmake
RUN apt-get -qq install -y python3-pip gcc cmake-curses-gui uuid-dev libssl-dev libsasl2-2 libsasl2-dev swig python-dev python3-dev ruby-dev libperl-dev

RUN useradd -r -M -d ${OPTDIR}${XQA} xqa
RUN chown -R xqa:xqa ${OPTDIR}${XQA}

USER xqa

WORKDIR ${OPTDIR}${XQA}

RUN pip3 install -r requirements.txt

ENV PYTHONPATH=${OPTDIR}/${XQA}

CMD ["/bin/sh", "-c", "python3 xqa/shard.py"]
