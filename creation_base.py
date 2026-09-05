import sqlite3

connexion = sqlite3.connect("stock.db")

curseur = connexion.cursor()

curseur.execute("""
CREATE TABLE IF NOT EXISTS munitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    stock INTEGER NOT NULL
)
""")

curseur.execute(
    "INSERT INTO munitions (nom, stock) VALUES (?, ?)",
    ("AN-M64A1 500 lb", 400)
)

curseur.execute(
    "INSERT INTO munitions (nom, stock) VALUES (?, ?)",
    ("AN-M65A1 1000 lb", 150)
)

curseur.execute(
    "INSERT INTO munitions (nom, stock) VALUES (?, ?)",
    ("HVAR", 120)
)

curseur.execute(
    "INSERT INTO munitions (nom, stock) VALUES (?, ?)",
    ("Réservoir 110 gal", 45)
)

connexion.commit()
connexion.close()

print("Base de données créée !")
