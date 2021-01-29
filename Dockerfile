FROM registry.access.redhat.com/ubi8/ubi-minimal

LABEL name="bayesian-api" \
      description="bayesian API server" \
      git-url="https://github.com/fabric8-analytics/fabric8-analytics-server" \
      git-path="/" \
      target-file="Dockerfile" \
      app-license="Apache 2.0"

ENV LANG=en_US.UTF-8 PYTHONDONTWRITEBYTECODE=1

ADD ./requirements.txt /coreapi/
ADD bayesian/ /coreapi/bayesian/

RUN microdnf install python3 git && microdnf clean all
RUN pip3 install --upgrade pip --no-cache-dir
RUN pip3 install -r /coreapi/requirements.txt --no-cache-dir

ADD bayesian/scripts/entrypoint.sh /coreapi/bayesian/scripts/entrypoint.sh

RUN chmod +x /coreapi/bayesian/scripts/entrypoint.sh

ENTRYPOINT ["/coreapi/bayesian/scripts/entrypoint.sh"]
