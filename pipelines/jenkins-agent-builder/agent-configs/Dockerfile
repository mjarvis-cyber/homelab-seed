FROM jenkins/inbound-agent:latest

ARG JENKINS_URL
ARG JENKINS_SECRET
ARG JENKINS_AGENT_NAME

ENV JENKINS_URL=${JENKINS_URL}
ENV JENKINS_AGENT_NAME=${JENKINS_AGENT_NAME}
ENV JENKINS_SECRET=${JENKINS_SECRET}
ENV JENKINS_AGENT_WORKDIR=/home/jenkins/agent

USER root
RUN apt update && curl -fsSL https://get.docker.com | sh
RUN usermod -aG docker jenkins
USER jenkins

ENTRYPOINT ["/usr/local/bin/jenkins-agent"]

