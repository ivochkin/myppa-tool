FROM ubuntu:trusty

MAINTAINER Stanislav Ivochkin "isn@extrn.org"

RUN apt-get update \
  && apt-get upgrade \
  && apt-get install --no-install-recommends --no-install-suggests -y \
    build-essential \
    binutils \
    fakeroot \
    cmake \
    git \
    autotools-dev \
    autoconf \
    autogen \
    automake \
    libtool \
    wget \
    curl
