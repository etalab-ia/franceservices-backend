FROM quay.io/keycloak/keycloak:21.0

WORKDIR /opt/keycloak

ADD ./keycloak/ssl/${KEYCLOAK_CERTIFICATE_FILE} .
ADD ./keycloak/keycloak-theme.jar /opt/keycloak/providers/keycloak-theme.jar

USER keycloak
ENTRYPOINT ["/opt/keycloak/bin/kc.sh", "start", \
    "--db=postgres", "--http-enabled=true", \
    "--hostname-strict=false", \
    "--proxy=passthrough", \
    "--hostname-path=/auth", \
    "--https-certificate-file=/etc/x509/https/tls.crt", \
    "--https-certificate-key-file=/etc/x509/https/tls.key", \
    "--spi-login-protocol-openid-connect-legacy-logout-redirect-uri=true"]
