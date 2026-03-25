from __future__ import annotations

import argparse
import random
from uuid import uuid4

from sqlalchemy import select

from app.db.models import User
from app.db.session import SessionLocal

FIRST_NAMES = [
    "Ana", "Bruno", "Carlos", "Daniela", "Eduardo", "Fernanda", "Gabriel", "Helena",
    "Igor", "Juliana", "Karina", "Leonardo", "Mariana", "Nicolas", "Otavio", "Paula",
    "Rafael", "Sabrina", "Thiago", "Vanessa",
]
LAST_NAMES = [
    "Silva", "Souza", "Oliveira", "Pereira", "Costa", "Rodrigues", "Almeida", "Lima",
    "Gomes", "Martins", "Araujo", "Melo", "Barbosa", "Rocha", "Dias", "Cardoso",
]


def build_user(index: int) -> User:
    nome = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    unique = uuid4().hex[:8]
    email = f"usuario{index}_{unique}@example.com"
    idade = random.randint(18, 65)
    return User(nome=nome, email=email, idade=idade)


def seed_users(count: int) -> int:
    inserted = 0
    with SessionLocal() as session:
        existing = session.scalar(select(User.id).limit(1))
        if existing is not None:
            return 0

        users = [build_user(index + 1) for index in range(count)]
        session.add_all(users)
        session.commit()
        inserted = len(users)
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Popula o banco com usuários de exemplo.")
    parser.add_argument("--count", type=int, default=50, help="Quantidade de usuários a inserir.")
    args = parser.parse_args()
    inserted = seed_users(args.count)
    if inserted == 0:
        print("Seed ignorado: já existem usuários cadastrados.")
        return
    print(f"Seed concluído: {inserted} usuários inseridos.")


if __name__ == "__main__":
    main()
