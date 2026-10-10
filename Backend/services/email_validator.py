import re

import dns.resolver


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)


class EmailValidator:

    def validate_format(
        self,
        email: str
    ) -> bool:

        if not email:
            return False

        return bool(
            EMAIL_PATTERN.fullmatch(
                email.strip()
            )
        )

    def validate_domain(
        self,
        email: str
    ) -> bool:

        if not self.validate_format(email):
            return False

        domain = email.rsplit(
            "@",
            1
        )[1]

        try:
            records = dns.resolver.resolve(
                domain,
                "MX"
            )

            return len(records) > 0

        except (
            dns.resolver.NoAnswer,
            dns.resolver.NXDOMAIN,
            dns.resolver.NoNameservers,
            dns.exception.Timeout
        ):
            return False

    def validate(
        self,
        email: str
    ) -> bool:

        return (
            self.validate_format(email)
            and
            self.validate_domain(email)
        )