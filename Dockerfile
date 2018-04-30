FROM debian:stretch

MAINTAINER james.hn.sears@gmail.com

RUN apt-get -qq update
RUN apt-get -qq install -y openjdk-8-jre

RUN apt-get install --reinstall -y locales
RUN sed -i 's/# en_GB.UTF-8 UTF-8/en_GB.UTF-8 UTF-8/' /etc/locale.gen
RUN locale-gen en_GB.UTF-8
ENV LANG en_GB.UTF-8
ENV LANGUAGE en_GB
ENV LC_ALL en_GB.UTF-8
RUN dpkg-reconfigure --frontend noninteractive locales

ARG OPTDIR=/opt/
ARG XQA=xqa-shard

RUN mkdir ${OPTDIR}/${XQA}
COPY src ${OPTDIR}/${XQA}
ADD requirements.txt ${OPTDIR}/${XQA}

RUN apt-get -qq remove cmake
RUN apt-get -qq install -y python3-pip gcc cmake-curses-gui uuid-dev libssl-dev libsasl2-2 libsasl2-dev swig python-dev python3-dev ruby-dev libperl-dev

RUN useradd -r -M -d ${OPTDIR}${XQA} xqa
RUN chown -R xqa:xqa ${OPTDIR}${XQA}

EXPOSE 1984

USER xqa

WORKDIR ${OPTDIR}${XQA}

RUN pip3 install -r requirements.txt

ENV PYTHONPATH=${OPTDIR}/${XQA}

ENTRYPOINT ["python3", "xqa/shard.py"]
