# Intentionally public identity used by the site UI, legal notices, and abuse handling.
# Edit only these two plain-text values; audit_public_release permits one occurrence here
# and flags unauthorized copies/obfuscations elsewhere.
PUBLIC_CONTACT_EMAIL = "asrinklcc@sely.tr"
PUBLIC_OPERATOR_NAME = "Asrın Kılıç"


def get_public_contact_email() -> str:
    return PUBLIC_CONTACT_EMAIL


def get_public_operator_name() -> str:
    return PUBLIC_OPERATOR_NAME
