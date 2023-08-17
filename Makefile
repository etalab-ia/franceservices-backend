
format_code:
	@# Format all python files
	pylsp.black --line-length 125 .

reorder_json_chunks:
	@# Reorder and clean the json database.
	# Usefull t compare different version of this file.
	cat ~/Downloads/files_as_chunks.json | jq 'sort_by(.xml_url) | map(del(.file))' > tmp.json


fetch_colab_notebooks:
	wget 'https://colab.research.google.com/drive/1_FQw20VjpKaE-Al-dh4jfVRtPawbD0fe' -O llama-finetuning-7b-4bit.ipynb
	wget 'https://colab.research.google.com/drive/148aZEs2-3hkCeTya1h4YPdfpqGIL5A4p' -O llama-inference-7b-4bit.ipynb

download_servicepublic_sheets:
	# Download xml files from:
	# https://www.data.gouv.fr/fr/datasets/service-public-fr-guide-vos-droits-et-demarches-particuliers/
	# https://www.data.gouv.fr/fr/datasets/service-public-fr-guide-vos-droits-et-demarches-entreprendre/
	# https://www.data.gouv.fr/fr/datasets/service-public-fr-guide-vos-droits-et-demarches-associations/
