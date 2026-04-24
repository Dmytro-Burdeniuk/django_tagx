from config.env import env

DATABASES = {
    "default": {
        # config for postgresql
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.str("POSTGRES_DB"),
        "USER": env.str("POSTGRES_USER"),
        "PASSWORD": env.str("POSTGRES_PASSWORD"),
        "HOST": env.str("POSTGRES_HOST", default="localhost"),
        "PORT": env.str("POSTGRES_PORT", default="5432"),
        # wraps every HTTP request in a transaction;  rolls back on exception
        "ATOMIC_REQUESTS": True,
        # reuse DB connections for N seconds instead of opening a new one per request
        "CONN_MAX_AGE": env.int("POSTGRES_CONN_MAX_AGE", default=60),
        # ping connection before reuse to avoid errors after DB restart
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            # wait for DB connection before raising an error
            "connect_timeout": 10,
            # kill any query running longer than 30s
            "options": "-c statement_timeout=30000",
            # ssl mode: disable | require | verify-ca | verify-full
            "sslmode": env.str("POSTGRES_SSL_MODE", default="disable"),
        },
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'