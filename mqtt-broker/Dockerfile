FROM eclipse-mosquitto

RUN apk add --no-cache tcpdump openssl

COPY mosquitto.conf /mosquitto/config/mosquitto.conf

# Generate CA
RUN mkdir -p /mosquitto/certs && \
    openssl req -new -x509 -days 365 -extensions v3_ca \
        -keyout /mosquitto/certs/ca.key \
        -out /mosquitto/certs/ca.crt \
        -subj "/CN=iot-farm-ca" \
        -nodes

# Generate broker key and CSR
RUN openssl genrsa -out /mosquitto/certs/broker.key 2048 && \
    openssl req -new -key /mosquitto/certs/broker.key \
        -out /mosquitto/certs/broker.csr \
        -subj "/CN=broker" \
        -nodes

# Sign broker certificate
RUN openssl x509 -req -days 365 \
        -in /mosquitto/certs/broker.csr \
        -CA /mosquitto/certs/ca.crt \
        -CAkey /mosquitto/certs/ca.key \
        -CAcreateserial \
        -out /mosquitto/certs/broker.crt
    
# Export CA cert for clients
RUN cp /mosquitto/certs/ca.crt /tmp/ca.crt

# Create password file
RUN mkdir -p /mosquitto/config && \
    mosquitto_passwd -c -b /mosquitto/config/passwd paddock-sensor-01 farm123 && \
    mosquitto_passwd -b /mosquitto/config/passwd cloud-subscriber farm123 && \
    mosquitto_passwd -b /mosquitto/config/passwd gippsland-weather-01 farm123 && \
    mosquitto_passwd -b /mosquitto/config/passwd paddock-gate-01 farm123 && \
    mosquitto_passwd -b /mosquitto/config/passwd iot-monitor farm123

# Create ACL file
RUN printf "\
user paddock-sensor-01\n\
topic write farm/paddock-sensor-01/telemetry\n\
\n\
user gippsland-weather-01\n\
topic write farm/gippsland-weather-01/telemetry\n\
\n\
user paddock-gate-01\n\
topic write farm/paddock-gate-01/telemetry\n\
topic read farm/paddock-gate-01/commands\n\
\n\
user cloud-subscriber\n\
topic read farm/#\n\
\n\
user iot-monitor\n\
topic read farm/#\n\
topic write farm/+/commands\n\
" > /mosquitto/config/acl

# Set permissions
RUN chown -R mosquitto:mosquitto /mosquitto/config /mosquitto/certs && \
    chmod 600 /mosquitto/config/passwd && \
    chmod 0700 /mosquitto/config/acl

EXPOSE 1883 8883