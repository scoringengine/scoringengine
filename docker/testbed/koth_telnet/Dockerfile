FROM ubuntu:latest

# Install Telnet server
RUN apt-get update && apt-get install -y \
    xinetd \
    telnetd

# Configure Telnet
COPY docker/testbed/telnet/files/telnet /etc/xinetd.d/telnet
COPY docker/testbed/telnet/files/startup.sh /startup.sh
RUN service xinetd restart

# Add test user
RUN \
    useradd -m ttesterson && \
    echo 'ttesterson:testpass' | chpasswd

# Add ownership file
COPY docker/testbed/telnet/files/ownership.txt /home/ttesterson/ownership.txt

EXPOSE 23

CMD ["/startup.sh"]