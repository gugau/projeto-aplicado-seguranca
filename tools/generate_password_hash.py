"""Gera um hash de senha sem colocar a senha na linha de comando."""

from getpass import getpass

from werkzeug.security import generate_password_hash


def main() -> None:
    password = getpass("Digite a senha: ")
    confirmation = getpass("Confirme a senha: ")

    if password != confirmation:
        raise SystemExit("As senhas não conferem.")
    if len(password) < 12:
        raise SystemExit("Use uma senha com pelo menos 12 caracteres.")

    print(generate_password_hash(password, method="scrypt"))


if __name__ == "__main__":
    main()
