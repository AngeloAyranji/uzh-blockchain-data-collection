FROM wurstmeister/kafka:2.13-2.8.1

# User permission build args
ARG KAFKA_USER=kafka
ARG KAFKA_UID=1000
ARG KAFKA_GID=1337
ENV KAFKA_USER $KAFKA_USER

VOLUME /kafka

# Starting kafka as non-root
# inspired by https://github.com/wurstmeister/kafka-docker/issues/403#issuecomment-506345960
RUN set -eux; \
    groupadd -r kafka --gid=$KAFKA_GID; \
    useradd -r -g kafka --uid=$KAFKA_UID $KAFKA_USER; \
    chown -hLR $KAFKA_USER:$KAFKA_GID $KAFKA_HOME; \
    chmod a+w -R $KAFKA_HOME; \
    chown -R $KAFKA_USER /usr/bin/*.sh

COPY entrypoint.sh /usr/bin/entrypoint.sh
RUN chmod a+x /usr/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
