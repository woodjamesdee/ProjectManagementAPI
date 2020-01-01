import os

def generate_secret_key():
    secret = os.urandom(24)

    with open("secret_key", "wb") as write_file:
        write_file.write(secret)