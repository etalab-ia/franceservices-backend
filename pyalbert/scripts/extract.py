#!/usr/bin/env python

import sys

sys.path.append(".")

from pprint import pprint

from evaluation import extract

answer = """ Bonjour.

Merci d'avoir partagé votre expérience sur SERVICES PUBLICS +. Votre témoignage nous aide à améliorer la qualité de nos services et des réponses affichées sur notre site.

je ne sais pas
je ne sais pas
je ne sais pas

77. hey

Nous sommes navrés d'apprendre que vous n'avez pas reçu de réponse à votre demande. Sachez que nous transmettons votre témoignage à nos équipes pour vous répondre comme nous le faisons quotidiennement pour plus de 40 000 témoignages.

Concernant votre demande, nous vous invitons www.test.de e http://www.frf.frrr.ze.de à contacter dede@de.De votre CAF par téléphone au 32 30 ou par courriel afin qu'ils puissent vous répondre précisément 0727272727 ou 09 09 23 23 23. ou +33 7 23 22 23 33.

test@gouv.fr da
test@data.gouv.fr.
site.fr
site.gouv.fr
test 10:30 test
23 règles.
vingt-trois règles.

$

Nous vous 10$ souhaitons une belle journée. 10 févrieR .  décembre 1999 d. novembre. 10 20  2$ ou 2% 1 10h12"""

data_x = extract(answer, how="content")
pprint(data_x)
