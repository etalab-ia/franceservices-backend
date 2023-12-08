
format_code:
	@# Format all python files
	pylsp.black --line-length 125 .

reorder_json_chunks:
	@# Reorder and clean the json database.
	# Usefull to compare different version of this file.
	cat ~/Downloads/files_as_chunks.json | jq 'sort_by(.url) | map(del(.file))' > tmp.json

info:
	@echo "Number of sheets: $$(cat _data/sheets_as_chunks.json | jq '.[] .url' | sort | uniq | wc -l)"
	@echo "Number of chunks: $$(cat _data/sheets_as_chunks.json | jq 'length')"
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

download_travailemploie_sheets:
	# wget https://github.com/SocialGouv/fiches-travail-data/raw/master/data/fiches-travail.json

institutions:
	cat _data/export-expa-c-riences.json  | jq  'map(.intitule_typologie_1) | unique | map(select(. != null))' > _data/institutions.json

acronyms_directory:
	@# to  _data/acronyms.text
	@# filter: Nantes, Montpellier, Toulouse, Secrétariat, Guangzhou, Fondatation
	@rg '"nom"'  _data/directory/national_data_directory.json | grep ')",$$' | cut -d: -f 2 | grep -oP '(?<=\").*(?=\")' | grep -E '\([A-Z0-9][0-9a-zA-Z]{2,}\)' | sort | uniq

acronyms_sp:
	@find -iname "*.xml" | xargs xmllint --xpath "//*[name()='OuSAdresser']/Titre/text() | //Fiche//Titre/text()" 2>/dev/null | grep -oE '.*\([A-Z0-9][0-9a-zA-Z]{2,}\)' | sort | uniq

acronyms: #acronyms_directory acronyms_sp
	# filter lines with more than one acronym
	cat acronyms_sp.txt acronyms_directory.txt > acronyms.txt
	cat acronyms.txt | sort | uniq > acronyms.1.txt
	grep -E '(.*\(.*){2,}' acronyms.1.txt > acronyms_dup.txt
	grep -v -F -f acronyms_dup.txt acronyms.1.txt > _data/acronyms.txt
	rm acronyms.txt acronyms.1.txt acronyms_dup.txt
	rm acronyms_sp.txt acronyms_directory.txt
	# @Warning: Duplicate have been process manually !
	# ./script/acronyms_to_json.py

sync_etalab_repo:
	rsync -avz --delete --exclude-from=".gitignore" -e "ssh -i ~/.ssh/etalab-dulac"  "../legal-information-assistant" adulac@datascience-01.infra.data.gouv.fr:~/

sync_etalab_repo_outscale_prod:
	rsync -avz --delete --exclude-from=".gitignore" -e "ssh -i ~/.ssh/etalab-dulac"  "../legal-information-assistant" adulac@171.33.114.210:~/

sync_etalab_repo_outscale_sand:
	rsync -avz --delete --exclude-from=".gitignore" -e "ssh -i ~/.ssh/etalab-dulac"  "../legal-information-assistant" adulac@217.75.171.132:~/

build_llama.cpp:
	git clone https://github.com/ggerganov/llama.cpp
	cd llama.cpp
	## @DEBUG/Upgrade
	git reset --hard "dadbed9" #Stick to the older version until gguf is fully supported
	# /
	make

convert_model_for_cpu:
	python llama.cpp/convert.py <model> -outfile <outfile>
	python llama.cpp/quantize <outfile> <outquantfile> q4_K

build_all_indexes: # not embeddings
	# elasticsearch
	python3 gpt.py index experiences --index-type bm25
	python3 gpt.py index sheets --index-type bm25
	python3 gpt.py index chunks --index-type bm25
	# meilisearch
	#python3 gpt.py index experiences --index-type bucket
	#sleep 3 # debug @async..
	#python3 gpt.py index sheets --index-type bucket
	#sleep 3
	#python3 gpt.py index chunks --index-type bucket
	# qdrant | requires _data/embeddings_*.npy
	python3 gpt.py index experiences --index-type e5
	python3 gpt.py index chunks --index-type e5

clean_all_indexex: # not embeddings
	# elasticsearch
	curl -XDELETE http://localhost:9202/experiences
	curl -XDELETE http://localhost:9202/sheets
	curl -XDELETE http://localhost:9202/chunks
	# meillisearch
	#curl -X DELETE http://localhost:7700/indexes/experiences
	#curl -X DELETE http://localhost:7700/indexes/sheets
	#curl -X DELETE http://localhost:7700/indexes/chunks
	# qdrant
	curl -X DELETE http://localhost:6333/collections/experiences
	curl -X DELETE http://localhost:6333/collections/chunks

list_indexes:
	# elasticsearch
	curl -X GET "http://localhost:9202/_cat/indices?v"
	# meilisearch
	#curl -X GET "http://localhost:7700/indexes" | jq
	# qdrant
	curl -X GET "http://localhost:6333/collections" | jq 

