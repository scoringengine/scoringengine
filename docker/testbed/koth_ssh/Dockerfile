FROM ubuntu:latest

# Make directory for openssh-server
RUN mkdir /var/run/sshd

# Install openssh-server
RUN apt-get update && apt-get install -y \
    openssh-server

# Add user
RUN \
    useradd -m ttesterson && \
    echo 'ttesterson:testpass' | chpasswd

# Copy ownership file
COPY docker/testbed/koth_ssh/ownership.txt /home/ttesterson/ownership.txt

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
