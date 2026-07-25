FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends sip-tester \
 && rm -rf /var/lib/apt/lists/*
COPY spoof.xml /root/spoof.xml
CMD ["sleep", "infinity"]
