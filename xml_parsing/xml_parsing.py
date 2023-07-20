import unicodedata

from bs4 import BeautifulSoup
import pandas as pd

from .files_management import get_xml_files


def get_xml_text_publications(xml_filepath: str) -> dict:
    """
    On utilise cette fonction pour créer un csv pour les fichiers qui commencent par N ou F.
    Ils correspondent soit à des fiches pratiques,
    soit à des questions réponses, soit à des fiches dossiers...

    """
    with open(xml_filepath, "r", encoding="utf-8") as xml_file:
        context = {}
        soup = BeautifulSoup(xml_file, "xml")
        context["title"] = soup.find("dc:title").get_text(" ", strip=True)
        context["title"] = context["title"]

        if (
            soup.find("Publication") is not None
            and "spUrl" in soup.find("Publication").attrs
        ):
            context["xml_url"] = soup.find("Publication")["spUrl"]
        else:
            context["xml_url"] = ""

        if soup.find("Introduction") is not None:
            context["introduction"] = soup.find("Introduction").get_text(
                " ", strip=True
            )
            context["introduction"] = context["introduction"].replace("\xa0", " ")
        else:
            context["introduction"] = ""

        if soup.find("SurTitre") is not None:
            context["surtitre"] = soup.find("SurTitre").get_text(" ", strip=True)
            context["surtitre"] = context["surtitre"]
        else:
            context["surtitre"] = ""

        if soup.find("dc:subject") is not None:
            context["subject"] = soup.find("dc:subject").get_text(" ", strip=True)
            context["subject"] = context["subject"]
        else:
            context["subject"] = ""

        context["theme"] = {}
        liste_themes = soup.find_all("Theme")
        for theme in liste_themes:
            theme_id = theme["ID"]
            theme_name = theme.find("Titre").get_text(" ", strip=True)
            theme_name = theme_name.replace("\xa0", " ")
            context["theme"][theme_name] = theme_id

        context["reference"] = {}
        liste_references = soup.find_all("Reference")
        for reference in liste_references:
            reference_url = reference["URL"]
            reference_title = reference.find("Titre").get_text(" ", strip=True)
            reference_title = reference_title.replace("\xa0", " ")
            context["reference"][reference_title] = reference_url

        context["ou_s_adresser"] = {}
        liste_ousadresser = soup.find_all("OuSAdresser")
        for ousadresser in liste_ousadresser:
            if ousadresser.find("RessourceWeb") is not None:
                ousadresser_var = ousadresser.find("RessourceWeb")["URL"]
            elif ousadresser.find("Texte") is not None:
                ousadresser_var = ousadresser.find("Texte").get_text(" ", strip=True)
                ousadresser_var = ousadresser_var.replace("\xa0", " ")
            ousadresser_title = ousadresser.find("Titre").get_text(" ", strip=True)
            ousadresser_title = ousadresser_title.replace("\xa0", " ")
            context["ou_s_adresser"][ousadresser_title] = ousadresser_var

        context["service_en_ligne"] = {}
        liste_serviceenligne = soup.find_all("ServiceEnLigne")
        for serviceenligne in liste_serviceenligne:
            if "URL" not in serviceenligne.attrs:
                continue
            serviceenligne_url = serviceenligne["URL"]
            serviceenligne_title = serviceenligne.find("Titre").get_text(
                " ", strip=True
            )
            serviceenligne_title = serviceenligne_title.replace("\xa0", " ")
            context["service_en_ligne"][serviceenligne_title] = serviceenligne_url

        context["liste_situations"] = {}
        if soup.find("ListeSituations") is not None:
            for situation in soup.find("ListeSituations").find_all("Situation"):
                situation_title = situation.find("Titre").get_text(" ", strip=True)
                situation_texte = situation.find("Texte").get_text(" ", strip=True)
                situation_title = situation_title.replace("\xa0", " ")
                situation_texte = situation_texte.replace("\xa0", " ")
                context["liste_situations"][situation_title] = situation_texte

        context["other_content"] = ""
        if soup.find("Publication") is not None:
            if soup.find("Publication").find("Texte", recursive=False) is not None:
                context["other_content"] = (
                    soup.find("Publication")
                    .find("Texte", recursive=False)
                    .get_text(" ", strip=True)
                )
                context["other_content"] = context["other_content"].replace("\xa0", " ")

        return context


def get_xml_text_publications_string(xml_filepath: str) -> dict:
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
    save_path: str = "datas/cleaned_xml/string_publications_xml_parsed.csv",
    to_string=True,
):
    if to_string:
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
    else:
        scrapped_context = pd.DataFrame(
            columns=[
                "file",
                "title",
                "xml_url",
                "introduction",
                "surtitre",
                "subject",
                "theme",
                "reference",
                "ou_s_adresser",
                "service_en_ligne",
                "liste_situations",
                "other_content",
            ]
        )

    xml_files = get_xml_files("datas/xml")
    for xml_file in xml_files:
        if not ("N" in xml_file.split("/")[-1] or "F" in xml_file.split("/")[-1]):
            # Permet de garder uniquement les fiches pratiques,
            # fiches questions-réponses, fiches thème, fiches dossier.
            continue
        if to_string:
            context = get_xml_text_publications_string(xml_file)
        else:
            context = get_xml_text_publications(xml_file)
        if not context:
            continue
        scrapped_context.loc[len(scrapped_context.index)] = [
            xml_file,
            *context.values(),
        ]

    scrapped_context.to_csv(save_path, sep=";", index=False)
