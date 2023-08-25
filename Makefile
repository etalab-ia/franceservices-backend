
format_code:
	@# Format all python files
	pylsp.black --line-length 125 .

reorder_json_chunks:
	@# Reorder and clean the json database.
	# Usefull t compare different version of this file.
	cat ~/Downloads/files_as_chunks.json | jq 'sort_by(.url) | map(del(.file))' > tmp.json

info:
	@echo "Number of sheets: $$(cat _data/xmlfiles_as_chunks.json | jq '.[] .url' | sort | uniq | wc -l)"
	@echo "Number of chunks: $$(cat _data/xmlfiles_as_chunks.json | jq 'length')"
	@echo "Number of questions (from sheets): $$(cat _data/questions.json | jq 'length')"
	@echo
	@cat _data/chunks.info

fetch_colab_notebooks:
	wget 'https://colab.research.google.com/drive/1_FQw20VjpKaE-Al-dh4jfVRtPawbD0fe' -O notebooks/llama-finetuning-7b-4bit.ipynb
	wget 'https://colab.research.google.com/drive/148aZEs2-3hkCeTya1h4YPdfpqGIL5A4p' -O notebooks/llama-inference-7b-4bit.ipynb

download_servicepublic_sheets:
	# Download xml files from:
	# https://www.data.gouv.fr/fr/datasets/service-public-fr-guide-vos-droits-et-demarches-particuliers/
	# https://www.data.gouv.fr/fr/datasets/service-public-fr-guide-vos-droits-et-demarches-entreprendre/
	# https://www.data.gouv.fr/fr/datasets/service-public-fr-guide-vos-droits-et-demarches-associations/

sync_etalab_repo:
	rsync -avz --delete --exclude-from=".gitignore" -e "ssh -i ~/.ssh/etalab-dulac"  "../legal-information-assistant" adulac@datascience-01.infra.data.gouv.fr:~/
