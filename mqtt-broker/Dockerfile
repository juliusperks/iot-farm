FROM eclipse-mosquitto
COPY mosquitto.conf /mosquitto/config/mosquitto.conf

RUN mosquitto_passwd -c -b /mosquitto/config/passwd paddock-sensor-01 farm123 && \
    mosquitto_passwd -b /mosquitto/config/passwd cloud-subscriber farm123

RUN echo "user paddock-sensor-01\ntopic write farm/paddock-sensor-01/telemetry\n\nuser cloud-subscriber\ntopic read farm/#" > /mosquitto/config/acl

EXPOSE 1883