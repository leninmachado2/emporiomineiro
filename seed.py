"""Carrega produtos do CSV no banco de dados (executa apenas se o banco estiver vazio)."""

import csv
from pathlib import Path
from app.database import criar_tabelas, SessionLocal
from app.models import Produto


def seed():
    criar_tabelas()
    db = SessionLocal()
    try:
        if db.query(Produto).count() > 0:
            print("Banco já possui produtos. Seed ignorado.")
            return

        csv_path = Path("data/produtos.csv")
        if not csv_path.exists():
            print(f"Arquivo não encontrado: {csv_path}")
            return

        total = 0
        with csv_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                db.add(Produto(
                    nome=row["nome"],
                    categoria=row["categoria"],
                    preco=float(row["preco"]),
                    quantidade_estoque=int(row["quantidadeEstoque"]),
                    descricao=row.get("descricao"),
                    caminho_imagem=row.get("caminhoImagem"),
                ))
                total += 1

        db.commit()
        print(f"✅ {total} produtos importados com sucesso.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
