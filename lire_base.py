import sqlite3

connexion = sqlite3.connect("stock.db")
curseur = connexion.cursor()

curseur.execute("SELECT * FROM munitions")

resultats = curseur.fetchall()

for ligne in resultats:
    print(ligne)

connexion.close()
