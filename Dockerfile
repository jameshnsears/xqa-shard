FROM ubuntu:bionic

RUN apt-get -qq update
RUN apt-get -qq install -y --no-install-recommends openjdk-11-jre python3-pip python3-dev

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
COPY requirements.txt ${OPTDIR}/${XQA}

RUN useradd -r -M -d ${OPTDIR}${XQA} xqa
RUN chown -R xqa:xqa ${OPTDIR}${XQA}

EXPOSE 1984

USER xqa

WORKDIR ${OPTDIR}${XQA}

RUN pip3 install -r requirements.txt

ENV PYTHONPATH=${OPTDIR}/${XQA}

ENTRYPOINT ["python3", "xqa/shard.py"]
