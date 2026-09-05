import sqlite3

connexion = sqlite3.connect("stock.db")
curseur = connexion.cursor()

curseur.execute("SELECT id, nom, stock FROM munitions")
munitions = curseur.fetchall()

print("STOCK ACTUEL")
print()

for munition in munitions:
    print(munition[0], "-", munition[1], ":", munition[2])

print()

choix = input("Quelle munition veux-tu utiliser ? ")

if choix.isdigit():

    choix = int(choix)

    curseur.execute(
        "SELECT id, nom, stock FROM munitions WHERE id = ?",
        (choix,)
    )

    munition = curseur.fetchone()

    if munition:

        demande = int(input("Combien veux-tu en utiliser ? "))

        if demande <= munition[2]:

            nouveau_stock = munition[2] - demande

            curseur.execute(
                "UPDATE munitions SET stock = ? WHERE id = ?",
                (nouveau_stock, choix)
            )

            connexion.commit()

            print()
            print("Nouveau stock de", munition[1], ":", nouveau_stock)

        else:
            print()
            print("Stock insuffisant !")

    else:
        print()
        print("Choix invalide !")

else:
    print()
    print("Choix invalide !")

connexion.close()
