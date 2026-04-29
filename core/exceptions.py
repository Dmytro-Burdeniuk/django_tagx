class AppError(Exception):
    default_message = "Application error."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)


class InvalidCredentialsError(AppError):
    default_message = "Invalid credentials."


class EmailAlreadyExistsError(AppError):
    default_message = "Email already registered."


class WeakPasswordError(AppError):
    default_message = "Password is too weak."