FROM ubuntu:latest

# Install Telnet server
RUN apt-get update && apt-get install -y \
    xinetd \
    telnetd

# Configure Telnet
COPY docker/testbed/telnet/files/telnet /etc/xinetd.d/telnet
RUN service xinetd restart

# Add test users
RUN \
    useradd -m ttesterson && \
    useradd -m rpeterson && \
    echo 'ttesterson:testpass' | chpasswd && \
    echo 'rpeterson:otherpass' | chpasswd

EXPOSE 23

# I couldn't get xinetd to log, so this is just a command that will run
# continuously so the container stays up. It's not ideal, but it works.
CMD ['tail', '-f', '/var/log/bootstrap.log']