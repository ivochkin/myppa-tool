FROM ubuntu:xenial

MAINTAINER Stanislav Ivochkin "isn@extrn.org"

RUN apt update \
  && apt-get upgrade \
  && apt install --no-install-recommends --no-install-suggests -y \
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
