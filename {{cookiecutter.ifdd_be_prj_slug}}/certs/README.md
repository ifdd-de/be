# Additional CA certificates

Place the PEM files of CAs this backend must trust here (`*.crt` or `*.pem`,
one certificate per file), typically `ca.crt` of the proxy instance
(`adm_01_certs.sh` there). The backend calls Keycloak (signing keys for token
validation) and the JSON-LD contexts under their public `https` URLs through
the proxy, and needs to trust its certificate for that.

The files are git-ignored and this directory is on the cruft skip list. They
are added to the system trust store at image build time, so rebuild the image
after a change. Never put private keys here: the directory is part of the
build context.
