FROM eclipse-mosquitto

RUN apk add --no-cache tcpdump

COPY mosquitto.conf /mosquitto/config/mosquitto.conf

RUN mkdir -p /mosquitto/config && \
    mosquitto_passwd -c -b /mosquitto/config/passwd paddock-sensor-01 farm123 && \
    mosquitto_passwd -b /mosquitto/config/passwd cloud-subscriber farm123 && \
    printf "user paddock-sensor-01\ntopic write farm/paddock-sensor-01/telemetry\n\nuser cloud-subscriber\ntopic read farm/#\n" > /mosquitto/config/acl && \
    chown -R mosquitto:mosquitto /mosquitto/config && \
    chmod 600 /mosquitto/config/passwd && \
    chmod 0700 /mosquitto/config/acl

EXPOSE 1883