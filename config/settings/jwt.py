from datetime import timedelta

from config.env import env

# For microservices: switch to RS256
# "ALGORITHM": "RS256",
# "SIGNING_KEY": env.str("JWT_PRIVATE_KEY"),   # RSA private key (PEM format)
# "VERIFYING_KEY": env.str("JWT_PUBLIC_KEY"),  # RSA public key (PEM format)

SIMPLE_JWT = {
    # symmetric signing — one key for sign + verify
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env.str("JWT_SIGNING_KEY"),

    # short-lived access token minimizes damage if leaked
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=15)),
    # refresh token survives longer but rotates on each use
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7)),

    # each /token/refresh issues a new refresh token — stolen token can only be used once
    "ROTATE_REFRESH_TOKENS": True,
    # old refresh token is blacklisted after rotation (blacklist)
    "BLACKLIST_AFTER_ROTATION": True,

    # reject tokens for deactivated users immediately
    "CHECK_USER_IS_ACTIVE": True,
    # Avoid DB write on every token request — use dedicated analytics instead
    "UPDATE_LAST_LOGIN": False,

    # standard RFC 6750 header format: Authorization: Bearer <token>
    "AUTH_HEADER_TYPES": ("Bearer",),
    # django header name — override if nginx forwards a non-standard header
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",

    # stable user identifier in payload (id)
    "USER_ID_FIELD": "id",
    # name of the claim inside JWT payload
    "USER_ID_CLAIM": "user_id",

    # only AccessToken is valid for authentication — refresh token cannot be used as access
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    # stores token type (access/refresh) in payload to prevent token confusion
    "TOKEN_TYPE_CLAIM": "token_type",

    # iss claim — identifies which service issued the token
    "ISSUER": env.str("JWT_ISSUER", default="django-template"),
    # aud claim — intended recipient; set explicitly when multiple services share tokens
    "AUDIENCE": env.str("JWT_AUDIENCE", default=None),

    # unique token ID — used by blacklist to track revoked tokens
    "JTI_CLAIM": "jti",
    # clock skew tolerance in seconds — protects against slight time differences between servers
    "LEEWAY": 10,

    # callable that checks if user is allowed to authenticate — default verifies is_active
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",

    # custom JSON encoder for non-standard payload types (UUID, Decimal, etc.) — None = default
    "JSON_ENCODER": None,
}