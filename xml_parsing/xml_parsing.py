import unicodedata

from bs4 import BeautifulSoup
import pandas as pd

from .files_management import get_xml_files


def get_xml_content(xml_filepath: str) -> dict:
    """
    On utilise cette fonction pour créer un csv pour les fichiers qui commencent par N ou F.
    Ils correspondent soit à des fiches pratiques,
    soit à des questions réponses, soit à des fiches dossiers...
    """
    with open(xml_filepath, "r", encoding="utf-8") as xml_file:
        context = {}
        soup = BeautifulSoup(xml_file, "xml")
        context["title"] = soup.find("dc:title").get_text(" ", strip=True)
        context["title"] = unicodedata.normalize("NFKC", context["title"])

        context["xml_url"] = ""
        if soup.find("Publication") is not None:
            if "spUrl" in soup.find("Publication").attrs:
                context["xml_url"] = soup.find("Publication")["spUrl"]

        if soup.find("Introduction") is not None:
            context["introduction"] = soup.find("Introduction").get_text(
                " ", strip=True
            )
            context["introduction"] = unicodedata.normalize(
                "NFKC", context["introduction"]
            )
        else:
            context["introduction"] = ""

        if soup.find("SurTitre") is not None:
            context["surtitre"] = soup.find("SurTitre").get_text(" ", strip=True)
            context["surtitre"] = unicodedata.normalize("NFKC", context["surtitre"])
        else:
            context["surtitre"] = ""

        if soup.find("dc:subject") is not None:
            context["subject"] = soup.find("dc:subject").get_text(" ", strip=True)
            context["subject"] = unicodedata.normalize("NFKC", context["subject"])
        else:
            context["subject"] = ""

        context["theme"] = ""
        liste_themes = soup.find_all("Theme")
        for theme in liste_themes:
            theme_name = theme.find("Titre").get_text(" ", strip=True)
            theme_name = unicodedata.normalize("NFKC", theme_name)
            if context["theme"] == "":
                context["theme"] = theme_name
            else:
                context["theme"] += ", " + theme_name

        context["liste_situations"] = ""
        if soup.find("ListeSituations") is not None:
            context["liste_situations"] = "Liste des situations : "
            for i, situation in enumerate(
                soup.find("ListeSituations").find_all("Situation")
            ):
                situation_title = situation.find("Titre").get_text(" ", strip=True)
                situation_texte = situation.find("Texte").get_text(" ", strip=True)
                situation_title = unicodedata.normalize("NFKC", situation_title)
                situation_texte = unicodedata.normalize("NFKC", situation_texte)

                context["liste_situations"] += (
                    " Cas n°"
                    + str(i + 1)
                    + " : "
                    + situation_title
                    + " : "
                    + situation_texte
                )

        context["other_content"] = ""
        if soup.find("Publication") is not None:
            if soup.find("Publication").find("Texte", recursive=False) is not None:
                context["other_content"] = (
                    soup.find("Publication")
                    .find("Texte", recursive=False)
                    .get_text(" ", strip=True)
                )
                context["other_content"] = unicodedata.normalize(
                    "NFKC", context["other_content"]
                )

        return context


def parse_xml(
    save_path_xml: str = "_data/csv_database/xml_parsed.csv",
    xml_3_folders_path: str = "_data/xml",
):
    scrapped_context = pd.DataFrame(
        columns=[
            "file",
            "title",
            "xml_url",
            "introduction",
            "surtitre",
            "subject",
            "theme",
            "liste_situations",
            "other_content",
        ]
    )

    xml_files = get_xml_files(xml_3_folders_path)
    current_percentage = 0
    for xml_index, xml_file in enumerate(xml_files):
        # Print the percentage of total time
        if (100 * xml_index) // (len(xml_files) - 1) > current_percentage:
            current_percentage = (100 * xml_index) // (len(xml_files) - 1)
            print(f"temps : {current_percentage} %")

        if not ("N" in xml_file.split("/")[-1] or "F" in xml_file.split("/")[-1]):
            # Permet de garder uniquement les fiches pratiques,
            # fiches questions-réponses, fiches thème, fiches dossier.
            continue
        context = get_xml_content(xml_file)
        if not context:
            continue
        scrapped_context.loc[len(scrapped_context.index)] = [
            xml_file,
            *context.values(),
        ]

    scrapped_context.to_csv(save_path_xml, sep=";", index=False)
