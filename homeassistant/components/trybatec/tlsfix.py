"""Remote server has a bad TLS configuration.

These workarounds will make to connection possible by fixing the 2 blocking issues:
    - legacy renegotiation
    - missing intermediate certificate in chain
See for TLS audit of the website:
    https://www.ssllabs.com/ssltest/analyze.html?d=portail.trybatec.fr&hideResults=on&latest.
"""
from __future__ import annotations

import os
import ssl
import tempfile

from OpenSSL import crypto  # pyOpenSSL
import certifi


class TrybatecBadTLS:
    """Helper to workaround bad service provider TLS config."""

    pem_cert = """-----BEGIN CERTIFICATE-----
MIIGEzCCA/ugAwIBAgIQfVtRJrR2uhHbdBYLvFMNpzANBgkqhkiG9w0BAQwFADCB
iDELMAkGA1UEBhMCVVMxEzARBgNVBAgTCk5ldyBKZXJzZXkxFDASBgNVBAcTC0pl
cnNleSBDaXR5MR4wHAYDVQQKExVUaGUgVVNFUlRSVVNUIE5ldHdvcmsxLjAsBgNV
BAMTJVVTRVJUcnVzdCBSU0EgQ2VydGlmaWNhdGlvbiBBdXRob3JpdHkwHhcNMTgx
MTAyMDAwMDAwWhcNMzAxMjMxMjM1OTU5WjCBjzELMAkGA1UEBhMCR0IxGzAZBgNV
BAgTEkdyZWF0ZXIgTWFuY2hlc3RlcjEQMA4GA1UEBxMHU2FsZm9yZDEYMBYGA1UE
ChMPU2VjdGlnbyBMaW1pdGVkMTcwNQYDVQQDEy5TZWN0aWdvIFJTQSBEb21haW4g
VmFsaWRhdGlvbiBTZWN1cmUgU2VydmVyIENBMIIBIjANBgkqhkiG9w0BAQEFAAOC
AQ8AMIIBCgKCAQEA1nMz1tc8INAA0hdFuNY+B6I/x0HuMjDJsGz99J/LEpgPLT+N
TQEMgg8Xf2Iu6bhIefsWg06t1zIlk7cHv7lQP6lMw0Aq6Tn/2YHKHxYyQdqAJrkj
eocgHuP/IJo8lURvh3UGkEC0MpMWCRAIIz7S3YcPb11RFGoKacVPAXJpz9OTTG0E
oKMbgn6xmrntxZ7FN3ifmgg0+1YuWMQJDgZkW7w33PGfKGioVrCSo1yfu4iYCBsk
Haswha6vsC6eep3BwEIc4gLw6uBK0u+QDrTBQBbwb4VCSmT3pDCg/r8uoydajotY
uK3DGReEY+1vVv2Dy2A0xHS+5p3b4eTlygxfFQIDAQABo4IBbjCCAWowHwYDVR0j
BBgwFoAUU3m/WqorSs9UgOHYm8Cd8rIDZsswHQYDVR0OBBYEFI2MXsRUrYrhd+mb
+ZsF4bgBjWHhMA4GA1UdDwEB/wQEAwIBhjASBgNVHRMBAf8ECDAGAQH/AgEAMB0G
A1UdJQQWMBQGCCsGAQUFBwMBBggrBgEFBQcDAjAbBgNVHSAEFDASMAYGBFUdIAAw
CAYGZ4EMAQIBMFAGA1UdHwRJMEcwRaBDoEGGP2h0dHA6Ly9jcmwudXNlcnRydXN0
LmNvbS9VU0VSVHJ1c3RSU0FDZXJ0aWZpY2F0aW9uQXV0aG9yaXR5LmNybDB2Bggr
BgEFBQcBAQRqMGgwPwYIKwYBBQUHMAKGM2h0dHA6Ly9jcnQudXNlcnRydXN0LmNv
bS9VU0VSVHJ1c3RSU0FBZGRUcnVzdENBLmNydDAlBggrBgEFBQcwAYYZaHR0cDov
L29jc3AudXNlcnRydXN0LmNvbTANBgkqhkiG9w0BAQwFAAOCAgEAMr9hvQ5Iw0/H
ukdN+Jx4GQHcEx2Ab/zDcLRSmjEzmldS+zGea6TvVKqJjUAXaPgREHzSyrHxVYbH
7rM2kYb2OVG/Rr8PoLq0935JxCo2F57kaDl6r5ROVm+yezu/Coa9zcV3HAO4OLGi
H19+24rcRki2aArPsrW04jTkZ6k4Zgle0rj8nSg6F0AnwnJOKf0hPHzPE/uWLMUx
RP0T7dWbqWlod3zu4f+k+TY4CFM5ooQ0nBnzvg6s1SQ36yOoeNDT5++SR2RiOSLv
xvcRviKFxmZEJCaOEDKNyJOuB56DPi/Z+fVGjmO+wea03KbNIaiGCpXZLoUmGv38
sbZXQm2V0TP2ORQGgkE49Y9Y3IBbpNV9lXj9p5v//cWoaasm56ekBYdbqbe4oyAL
l6lFhd2zi+WJN44pDfwGF/Y4QA5C5BIG+3vzxhFoYt/jmPQT2BVPi7Fp2RBgvGQq
6jG35LWjOhSbJuMLe/0CjraZwTiXWTb2qHSihrZe68Zk6s+go/lunrotEbaGmAhY
LcmsJWTyXnW0OMGuf1pGg+pRyrbxmRE1a6Vqe8YAsOf4vmSyrcjC8azjUeqkk+B5
yOGBQMkKW+ESPMFgKuOXwIlCypTPRpgSabuY0MLTDXJLR27lk8QyKGOHQ+SwMj4K
00u/I5sUKUErmgQfky3xxzlIPK1aEn8=
-----END CERTIFICATE-----
"""

    def __init__(self) -> None:
        """Prepare the TLS helper.

        It will:
        - creating a custom CA store (custom_store_path attribute)
        - copy original certifi CA store into it
        - inject missing intermediate certificate into it
        - create a custom SSL context using the custom store and allowing unsafe renegotiation (ssl_ctx attribute).
        """
        # Load certificate and extract infos
        cert = crypto.load_certificate(
            crypto.FILETYPE_PEM, self.pem_cert.encode("ascii")
        )
        issuer = cert.get_issuer()
        issued_by = issuer.CN
        subject = cert.get_subject()
        issued_to = subject.CN
        serial = cert.get_serial_number()
        md5 = cert.digest("md5").decode("ascii")
        sha1 = cert.digest("sha1").decode("ascii")
        sha256 = cert.digest("sha256").decode("ascii")
        # Prepare local store
        custom_store_fd, self.custom_store_path = tempfile.mkstemp(
            prefix="cacert-trybatec_", suffix=".pem"
        )
        with os.fdopen(custom_store_fd, "w") as custom_store:
            # Copy original store into custom store
            with open(certifi.where(), encoding="ascii") as original_store:
                for line in original_store:
                    custom_store.write(line)
            # Inject intermediate certificate into custom store
            ## Comment section
            custom_store.write(
                "# Trybatec Shitty Web Server fix: add missing intermediate to store\n"
            )
            custom_store.write(f"# Issuer: {issued_by}\n")
            custom_store.write(f"# Subject: {issued_to}\n")
            custom_store.write(f"# Serial: {serial}\n")
            custom_store.write(f"# MD5 Fingerprint: {md5}\n")
            custom_store.write(f"# SHA1 Fingerprint: {sha1}\n")
            custom_store.write(f"# SHA256 Fingerprint: {sha256}\n")
            ## PEM Certificate section
            custom_store.write(self.pem_cert)
            custom_store.write("\n")
        # Prepare SSL context
        self.ssl_ctx = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH,
            # aiohttp does not use this store by default, but this is the one we can inject our intermediate into.
            # Fix for:
            # [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
            cafile=self.custom_store_path,
        )
        # fix for SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED
        self.ssl_ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT

    def cleanup(self):
        """Remove the custom CA store from disk."""
        if os.path.exists(self.custom_store_path):
            os.remove(self.custom_store_path)
