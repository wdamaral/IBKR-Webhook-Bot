import bcrypt
import settings


def hashSecret(secret):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(secret.encode(), salt)

    return hashed


def compareSecret(secret, isAdmin=False):
    # get secret from vault
    if (isAdmin):
        return bcrypt.checkpw(secret.encode(), settings.admin_secret_key.encode())

    return bcrypt.checkpw(secret.encode(), settings.alert_secret_key.encode())
