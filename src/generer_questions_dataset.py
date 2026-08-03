"""
Generation automatique de questions supplementaires pour atteindre le
livrable S3 (>= 300 interactions reelles, section 9 du cahier des
charges), avec une repartition EQUILIBREE entre categories (aucune
categorie ne doit dominer le dataset, pour une analyse exploratoire
representative en S4).

Combine plusieurs approches :
1. Detection AUTOMATIQUE des villes et institutions reellement presentes
   dans le corpus (verification litterale, normalisee casse/accents),
   pour generer des questions authentiques sans deviner a l'aveugle.
2. Questions codees en dur, variees : reglementation, definitions,
   chiffres, comparaisons, questions ambigues et hors-perimetre
   (cf. cahier des charges section 3.2, Option A).
3. Les questions liees aux villes sont PLAFONNEES (GEO_MAX) et reparties
   entre deux categories differentes (geo_tabulaire : listing direct ;
   scenario : conseil/comparaison), pour eviter qu'une seule categorie
   ne represente une part disproportionnee du dataset.

Usage :
    python src/generer_questions_dataset.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rag_agent import charger_tous_les_chunks, supprimer_accents

OUTPUT_FILE = Path("questions_dataset_S3.csv")

# Nombre total d'interactions REELLES visees pour S3 (35 deja faites en S2
# + celles generees ici). Le cahier des charges (section 9, planning S3)
# demande explicitement >= 300 comme livrable de cette semaine.
TOTAL_INTERACTIONS_VISE = 310
DEJA_REALISEES_S2 = 35

# Plafond STRICT du nombre de questions purement geo_tabulaire (listing
# direct par ville), pour eviter qu'une seule categorie ne domine le
# dataset (probleme reel rencontre : 201/310 = 65% lors d'un premier
# essai sans plafond).
GEO_MAX = 60

VILLES_CANDIDATES = [
    "Yaounde", "Douala", "Bafoussam", "Bamenda", "Garoua", "Maroua",
    "Ngaoundere", "Bertoua", "Ebolowa", "Buea", "Limbe", "Kribi", "Edea",
    "Foumban", "Dschang", "Kumba", "Nkongsamba", "Sangmelima", "Bafia",
    "Mbalmayo", "Meiganga", "Guider", "Mokolo", "Koussere", "Mora",
    "Tibati", "Bogo", "Yagoua", "Mbouda", "Bandjoun", "Bafang", "Fundong",
    "Wum", "Bali", "Batouri", "Abong-Mbang", "Akonolinga", "Obala",
    "Nanga-Eboko", "Monatele", "Ntui", "Eseka", "Loum", "Manjo", "Melong",
    "Penja", "Tiko", "Muyuka", "Mamfe", "Ndop", "Nkambe", "Kaele",
    "Mindif", "Gazawa", "Guiguidis", "Founangue",
]

TEMPLATES_GEO = [
    "Quelles sont les microfinances presentes a {ville} ?",
    "Peux-tu me lister les etablissements de microfinance situes a {ville} ?",
    "Y a-t-il des etablissements de microfinance agrees a {ville} ?",
    "Quels sont les EMF localises dans la ville de {ville} ?",
]

TEMPLATES_SCENARIO = [
    "Si j'habite a {ville}, vers quel type d'etablissement de microfinance devrais-je me tourner ?",
    "Recommande-moi une cooperative d'epargne adaptee si je suis base a {ville}.",
    "Quelles options de microfinance conseillerais-tu pour quelqu'un vivant a {ville} ?",
    "Je cherche a ouvrir un compte d'epargne a {ville}, que me suggeres-tu ?",
]

QUESTIONS_REGLEMENTATION_SUPPLEMENTAIRES = [
    "Quel organisme delivre l'agrement des etablissements de microfinance en zone CEMAC ?",
    "Quelles sont les obligations comptables d'un etablissement de microfinance ?",
    "Que signifie le sigle COBAC ?",
    "Que signifie le sigle CEMAC ?",
    "Que signifie le sigle UMAC ?",
    "Un etablissement de microfinance peut-il collecter l'epargne du grand public ?",
    "Quelles sanctions la COBAC peut-elle appliquer a un EMF en infraction ?",
    "Quelle est la difference entre un EMF et une banque commerciale ?",
    "Un EMF de premiere categorie peut-il servir des clients non-membres ?",
    "Quel est le role du Conseil National du Credit (CNC) ?",
    "Qu'est-ce qu'un numero d'immatriculation au CNC ?",
    "Quelles informations doit contenir une demande d'agrement EMF ?",
    "Comment un EMF change-t-il de categorie ?",
    "Quelles sont les regles de gouvernance imposees aux dirigeants d'un EMF ?",
    "Quel est le capital minimum pour un EMF de troisieme categorie ?",
    "Quel est le capital minimum pour un EMF de deuxieme categorie ?",
    "La COBAC supervise-t-elle aussi les banques commerciales ?",
    "Qu'est-ce que le fonds de garantie des EMF ?",
    "Quels documents un EMF doit-il transmettre a la COBAC chaque annee ?",
    "Un EMF peut-il operer dans plusieurs pays de la zone CEMAC ?",
    "Quel texte reglemente actuellement la microfinance en zone CEMAC ?",
    "Qui compose le conseil d'administration d'un EMF de premiere categorie ?",
    "Quelles sont les regles de ratio prudentiel imposees a un EMF ?",
    "Un EMF doit-il publier ses comptes annuels ?",
    "Quel est le role du commissaire aux comptes (CAC) dans un EMF ?",
    "Comment la COBAC controle-t-elle les EMF sur le terrain ?",
    "Un EMF peut-il faire faillite ? Que se passe-t-il alors ?",
    "Quelles obligations de transparence un EMF a-t-il envers ses membres ?",
    "Existe-t-il une assurance-depot pour les clients des EMF ?",
    "Quel est le processus de retrait d'agrement d'un EMF ?",
    "Un dirigeant d'EMF peut-il cumuler plusieurs mandats ?",
    "Comment se fait le controle interne dans un EMF ?",
    "Quelles regles s'appliquent aux operations de credit entre EMF ?",
    "Un EMF peut-il fusionner avec un autre EMF ?",
    "Quel role joue le ministere des Finances dans la supervision des EMF ?",
    "Comment un client peut-il porter plainte contre un EMF ?",
    "Quels criteres definissent la solvabilite d'un EMF ?",
    "Existe-t-il un delai de traitement standard pour une demande d'agrement ?",
    "Quelles obligations de formation existent pour les dirigeants d'EMF ?",
    "Un EMF etranger peut-il s'implanter au Cameroun sans agrement local ?",
]

QUESTIONS_DEFINITIONS_REFORMULEES = [
    "Explique-moi simplement ce qu'est la microfinance.",
    "A quoi sert le microcredit concretement ?",
    "Comment fonctionne une tontine traditionnelle ?",
    "Quelle est la difference entre microcredit et credit bancaire classique ?",
    "Pourquoi la microfinance existe-t-elle ?",
    "Qui sont les beneficiaires typiques de la microfinance ?",
    "Quels sont les risques de la microfinance pour les emprunteurs ?",
    "La microfinance reduit-elle vraiment la pauvrete ?",
    "Quels services propose typiquement un EMF a ses clients ?",
    "Quelle est l'origine historique du microcredit ?",
    "Quels sont les avantages d'une tontine par rapport a une banque ?",
    "Comment une association collective d'epargne fonctionne-t-elle ?",
    "Quels sont les acteurs principaux du secteur de la microfinance en zone CEMAC ?",
    "Quelle est la place des femmes dans les programmes de microfinance ?",
    "Quels sont les criteres pour qu'un EMF soit considere solide financierement ?",
    "Qu'est-ce que la finance solidaire concretement ?",
    "Quelle est la difference entre finance solidaire et microfinance ?",
    "Comment fonctionne le systeme bancaire classique en comparaison d'un EMF ?",
    "Qu'est-ce qu'un club d'investisseurs solidaires ?",
    "Quels sont les debats autour de la delimitation du microcredit ?",
    "Le microcredit doit-il cibler en priorite les plus pauvres ?",
    "Quels scandales ont deja touche le secteur de la microfinance ?",
    "Comment le CGAP definit-il la bonne utilisation de l'argent des donateurs ?",
    "Quels sont les criteres d'exploitation abusive des beneficiaires d'IMF ?",
    "Quelle est l'evolution recente du cadre juridique de la microfinance en CEMAC ?",
    "Qu'est-ce qu'une societe de capital-risque solidaire ?",
    "Quels types de clubs d'investisseurs existent en finance solidaire ?",
    "Le microcredit favorise-t-il vraiment l'inclusion bancaire ?",
    "Quelles sont les limites du microcredit pour les plus pauvres ?",
    "Comment mesure-t-on l'efficacite technique d'une institution financiere ?",
]

INSTITUTIONS_A_VERIFIER = [
    ("CECIAC", "Qu'est-ce que la Cooperative d'Epargne et de Credit et d'Investissement Agricole du Cameroun ?"),
    ("SOCEC", "Qu'est-ce que la Societe Cooperative d'Epargne et de Credit SOCEC ?"),
    ("CAPFINANCE", "Qu'est-ce que le CAPFINANCE ?"),
    ("People Finance", "Qu'est-ce que le reseau People Finance ?"),
    ("Caisse Camerounaise d'Epargne et de Credit", "Qu'est-ce que la Caisse Camerounaise d'Epargne et de Credit ?"),
    ("CVECA et CECA de l'Extreme-Nord", "Qu'est-ce que la Societe Cooperative Regionale des CVECA et CECA de l'Extreme-Nord ?"),
    ("CREDIT DU SAHEL", "Qu'est-ce que le Credit du Sahel S.A ?"),
    ("FODIFES", "Qu'est-ce que le Fonds de Financement du Developpement Social (FODIFES) ?"),
    ("Siloe", "Qu'est-ce que la Cooperative Siloe Epargne Financiere au Cameroun ?"),
    ("ADEC", "Qu'est-ce que l'African Development Credit (ADEC) ?"),
    ("MUCADEC", "Qu'est-ce que la Mutuelle Camerounaise d'Epargne et Credit MUCADEC ?"),
    ("MUFFEDYC", "Qu'est-ce que la Mutuelle Financiere des Femmes Dynamiques du Cameroun ?"),
    ("CEPI SA", "Qu'est-ce que les Caisses d'Epargne Populaire et d'Investissement SA ?"),
    ("FIRSTTRUST", "Qu'est-ce que First Trust Savings and Loans ?"),
    ("CDECA", "Qu'est-ce que la Caisse de Developpement d'Epargne et de Credit d'Afrique ?"),
]

QUESTIONS_CHIFFREES_SUPPLEMENTAIRES = [
    "Quel est le montant total des depots collectes par les EMF en zone CEMAC en 2023 ?",
    "Quel est le montant de l'encours des credits accordes par les EMF en zone CEMAC en 2023 ?",
    "Combien y a-t-il d'EMF de deuxieme categorie en zone CEMAC ?",
    "Combien y a-t-il d'EMF de troisieme categorie en zone CEMAC ?",
    "Quel est le ratio credit/depots dans le secteur de la microfinance CEMAC ?",
    "Combien d'etablissements de microfinance existent en Guinee Equatoriale ?",
    "Quelle proportion des EMF sont des reseaux plutot que des etablissements independants ?",
    "Combien d'EMF au total etaient agrees et en activite en zone CEMAC recemment ?",
    "Quel pourcentage des EMF de la zone CEMAC sont bases au Cameroun ?",
    "Quelle est l'evolution du nombre d'EMF entre 2010 et 2010 en Guinee Equatoriale ?",
    "Quel est le nombre moyen de clients par EMF de premiere categorie ?",
    "Quel pourcentage des depots CEMAC est concentre sur les EMF de deuxieme categorie ?",
    "Combien de reseaux d'EMF existent en zone CEMAC ?",
    "Quel est le taux de croissance annuel du secteur de la microfinance CEMAC ?",
    "Quelle est la part de marche des trois plus grands reseaux d'EMF au Cameroun ?",
]

QUESTIONS_AMBIGUES = [
    "Et pour les femmes ?",
    "C'est risque ou pas ?",
    "Ca marche comment exactement ?",
    "Est-ce que c'est fiable ?",
    "Combien ca coute ?",
    "Qui peut en beneficier ?",
    "C'est mieux qu'une banque ?",
    "Depuis quand ca existe ?",
    "Est-ce accessible a tout le monde ?",
    "Quels sont les inconvenients ?",
    "Et si je n'ai pas de garantie ?",
    "C'est long comme demarche ?",
    "Ca vaut le coup ?",
    "Et pour les jeunes entrepreneurs ?",
    "Qu'est-ce qui change par rapport a avant ?",
    "C'est pareil partout ?",
    "Et en cas de probleme ?",
    "Ca depend de quoi ?",
    "Il y a des conditions particulieres ?",
    "Et concretement, ca donne quoi ?",
]

QUESTIONS_HORS_PERIMETRE_SUPPLEMENTAIRES = [
    "Quelle heure est-il a Yaounde en ce moment ?",
    "Peux-tu me donner une recette de ndole ?",
    "Qui a gagne la derniere Coupe d'Afrique des Nations ?",
    "Peux-tu traduire 'microfinance' en anglais ?",
    "Quel est le taux de change actuel FCFA/Euro ?",
    "Peux-tu m'aider a rediger un CV ?",
    "Quelle est la capitale de la France ?",
    "Combien font 15 fois 24 ?",
    "Peux-tu me raconter une blague ?",
    "Quel est le prix moyen d'un billet d'avion Douala-Paris ?",
    "Quelle est la population totale du Cameroun ?",
    "Peux-tu me donner la meteo de la semaine a Douala ?",
    "Quel est le meilleur restaurant de Yaounde ?",
    "Comment configurer une adresse email professionnelle ?",
    "Quel est le classement FIFA actuel du Cameroun ?",
    "Peux-tu m'expliquer la theorie de la relativite ?",
    "Quelles sont les meilleures universites du Cameroun ?",
    "Comment planter du manioc ?",
    "Quel est le prix d'un sac de ciment a Douala ?",
    "Peux-tu me conseiller un livre sur l'histoire du Cameroun ?",
]

QUESTIONS_COMPARAISON = [
    "Quelle est la difference entre un EMF de premiere et de troisieme categorie ?",
    "En quoi une tontine differe-t-elle d'un EMF de premiere categorie ?",
    "Compare le role de la COBAC a celui d'une banque centrale nationale.",
    "Quelle est la difference entre le microcredit et le pret bancaire classique ?",
    "En quoi CamCCUL et MC2 se ressemblent-ils ou different-ils ?",
    "Compare les reseaux MUFID et CVECA/CECA.",
    "Quelle est la difference entre une cooperative et une societe anonyme dans le secteur EMF ?",
    "En quoi la finance solidaire differe-t-elle de la microfinance classique ?",
    "Compare les obligations reglementaires d'un EMF de deuxieme et troisieme categorie.",
    "Quelle est la difference entre un reseau d'EMF et un EMF independant ?",
    "En quoi le systeme bancaire CEMAC differe-t-il du systeme bancaire francais ?",
    "Compare l'agrement d'un EMF a celui d'une banque commerciale.",
    "Quelle est la difference entre Context Precision et Context Recall en evaluation RAG ?",
    "En quoi un EMF urbain differe-t-il d'un EMF rural en zone CEMAC ?",
    "Compare les avantages et inconvenients du microcredit par rapport a la tontine.",
    "Quelle est la difference entre un depot a vue et un depot d'epargne dans un EMF ?",
    "En quoi les regles prudentielles CEMAC different-elles selon la categorie d'EMF ?",
    "Compare la gouvernance d'un EMF mutualiste et d'un EMF societe anonyme.",
    "Quelle est la difference entre le Cameroun et la Guinee Equatoriale en nombre d'EMF ?",
    "Compare le role du CNC a celui de la COBAC.",
]


def detecter_institutions_reelles():
    print("Verification des institutions dans le corpus (insensible casse/accents)...")
    _, tous_les_documents = charger_tous_les_chunks()
    texte_complet_normalise = supprimer_accents(
        " ".join(doc.page_content for doc in tous_les_documents).lower()
    )

    institutions_confirmees = []
    institutions_exclues = []
    for token, question in INSTITUTIONS_A_VERIFIER:
        token_normalise = supprimer_accents(token.lower())
        if token_normalise in texte_complet_normalise:
            institutions_confirmees.append(question)
        else:
            institutions_exclues.append(token)

    print(f"{len(institutions_confirmees)}/{len(INSTITUTIONS_A_VERIFIER)} institutions confirmees dans le corpus")
    if institutions_exclues:
        print(f"Institutions NON trouvees, questions exclues : {institutions_exclues}")

    return institutions_confirmees


def detecter_villes_reelles():
    print("Chargement des chunks pour detecter les villes reellement presentes...")
    _, tous_les_documents = charger_tous_les_chunks()
    texte_complet_normalise = supprimer_accents(
        " ".join(doc.page_content for doc in tous_les_documents).lower()
    )

    villes_trouvees = [
        v for v in VILLES_CANDIDATES
        if supprimer_accents(v.lower()) in texte_complet_normalise
    ]
    print(f"{len(villes_trouvees)} villes detectees sur {len(VILLES_CANDIDATES)} candidates : "
          f"{villes_trouvees}")
    return villes_trouvees


def generer_questions_par_ville(villes, templates, nombre_cible, categorie):
    """Genere des questions en cyclant villes x templates, jusqu'a
    atteindre nombre_cible, sans jamais depasser ce plafond."""
    questions = []
    if not villes or nombre_cible <= 0:
        return questions
    index_ville = 0
    index_template = 0
    while len(questions) < nombre_cible:
        ville = villes[index_ville % len(villes)]
        template = templates[index_template % len(templates)]
        questions.append((categorie, template.format(ville=ville)))
        index_ville += 1
        if index_ville % len(villes) == 0:
            index_template += 1
    return questions


def main():
    villes = detecter_villes_reelles()
    questions_institutions_verifiees = detecter_institutions_reelles()

    questions_fixes = (
        [("reglementation", q) for q in QUESTIONS_REGLEMENTATION_SUPPLEMENTAIRES]
        + [("definitions", q) for q in QUESTIONS_DEFINITIONS_REFORMULEES]
        + [("institutions", q) for q in questions_institutions_verifiees]
        + [("chiffres", q) for q in QUESTIONS_CHIFFREES_SUPPLEMENTAIRES]
        + [("ambigue", q) for q in QUESTIONS_AMBIGUES]
        + [("hors_perimetre", q) for q in QUESTIONS_HORS_PERIMETRE_SUPPLEMENTAIRES]
        + [("comparaison", q) for q in QUESTIONS_COMPARAISON]
    )

    nombre_a_generer = TOTAL_INTERACTIONS_VISE - DEJA_REALISEES_S2
    nombre_geo = min(GEO_MAX, max(0, nombre_a_generer - len(questions_fixes)))
    nombre_scenario = max(0, nombre_a_generer - len(questions_fixes) - nombre_geo)

    if not villes and (nombre_geo > 0 or nombre_scenario > 0):
        print("\n/!\\ ATTENTION : aucune ville detectee dans le corpus. "
              "Verifie que l'index FAISS est bien construit.")

    questions_geo = generer_questions_par_ville(villes, TEMPLATES_GEO, nombre_geo, "geo_tabulaire")
    questions_scenario = generer_questions_par_ville(villes, TEMPLATES_SCENARIO, nombre_scenario, "scenario")

    toutes_les_questions = questions_geo + questions_scenario + questions_fixes

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "categorie", "question"])
        for i, (categorie, question) in enumerate(toutes_les_questions, start=1):
            writer.writerow([f"S3-{i:03d}", categorie, question])

    total_final = DEJA_REALISEES_S2 + len(toutes_les_questions)

    print(f"\n{len(toutes_les_questions)} questions supplementaires generees dans {OUTPUT_FILE}")
    print(f"\nRepartition par categorie :")
    from collections import Counter
    compteur = Counter(cat for cat, _ in toutes_les_questions)
    for categorie, nombre in sorted(compteur.items(), key=lambda x: -x[1]):
        pourcentage = 100 * nombre / len(toutes_les_questions)
        print(f"  - {categorie:20s} : {nombre:3d} ({pourcentage:.1f}%)")

    print(f"\nTotal avec les {DEJA_REALISEES_S2} questions deja faites en S2 : {total_final}")

    if total_final < 300:
        print(f"\n/!\\ ATTENTION : {total_final} < 300 (livrable explicite de S3). "
              f"Il manque {300 - total_final} interactions. "
              f"Ajoute des questions dans les listes fixes, puis relance.")
    else:
        print("Objectif du livrable S3 (>= 300) atteint, avec repartition equilibree.")


if __name__ == "__main__":
    main()