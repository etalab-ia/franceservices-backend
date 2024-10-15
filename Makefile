.PHONY: help version build push clean publish

help:
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

#
# Build
#

version: pyproject.toml
	@version=$$(grep -Po '(?<=version = ")[^"]*' pyproject.toml); \
		if [ -z "$$version" ]; then \
		echo "Version not found in pyproject.toml"; \
		exit 1; \
	fi; \
	echo "__version__ = \"$$version\"" > pyalbert/_version.py

build: version
	python -m build

push: build
	twine upload dist/*

publish: push clean

clean:
	rm -rf dist build *.egg-info version.py

#
# Utils
#

format_code_black:
	@# Format all python files
	pylsp.black --line-length 100 .

format_code_ruff:
	@# Format all python files
	ruff format --line-length 100 .

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

fetch_openai_openapi:
	wget https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml

fetch_colab_notebooks:
	wget 'https://colab.research.google.com/drive/1_FQw20VjpKaE-Al-dh4jfVRtPawbD0fe' -O notebooks/llama-finetuning-7b-4bit.ipynb
	wget 'https://colab.research.google.com/drive/148aZEs2-3hkCeTya1h4YPdfpqGIL5A4p' -O notebooks/llama-inference-7b-4bit.ipynb

download_experiences:
	wget https://opendata.plus.transformation.gouv.fr/api/explore/v2.1/catalog/datasets/export-expa-c-riences/exports/json

download_servicepublic_sheets:
	# Download xml files from:
	# https://www.data.gouv.fr/fr/datasets/service-public-fr-guide-vos-droits-et-demarches-particuliers/
	# https://www.data.gouv.fr/fr/datasets/service-public-fr-guide-vos-droits-et-demarches-entreprendre/
	# https://www.data.gouv.fr/fr/datasets/service-public-fr-guide-vos-droits-et-demarches-associations/

download_travailemploie_sheets:
	# wget https://github.com/SocialGouv/fiches-travail-data/raw/master/data/fiches-travail.json

institutions:
	cat _data/export-expa-c-riences.json  | jq  'map(.intitule_typologie_1) | unique | map(select(. != null))' > _data/institutions.json

mfs_organizations:
	wget https://www.data.gouv.fr/fr/datasets/r/afc3f97f-0ef5-429b-bf16-7b7876d27cd4 -O _data/liste-mfs.csv
	cat _data/liste-mfs.csv | grep '^"[0-9]*"' | awk -v FPAT='([^,]+)|(\"[^\"]+\")' '{print "{\"id\":"$$1", \"name\":"$$3"}"}' | jq -s > _data/liste-mfs.json
	rm -f _data/liste-mfs.csv

acronyms_directory:
	@# ->  acronyms_directory.text
	@rg '"nom"'  _data/directory/national_data_directory.json | grep ')",$$' | cut -d: -f 2 | grep -oP '(?<=\").*(?=\")' | grep -E '\([A-Z0-9][0-9a-zA-Z]{2,}\)' | sort | uniq

acronyms_sp:
	@# ->  acronyms_sp.text
	@find -iname "*.xml" | xargs xmllint --xpath "//*[name()='OuSAdresser']/Titre/text() | //Fiche//Titre/text()" 2>/dev/null | grep -oE '.*\([A-Z0-9][0-9a-zA-Z]{2,}\)' | sort | uniq

acronyms: acronyms_directory acronyms_sp
	# filter lines with more than one acronym
	cat acronyms_sp.txt acronyms_directory.txt > acronyms.txt
	cat acronyms.txt | sort | uniq > acronyms.1.txt
	grep -E '(.*\(.*){2,}' acronyms.1.txt > acronyms_dup.txt
	grep -v -F -f acronyms_dup.txt acronyms.1.txt > _data/acronyms.txt
	rm acronyms.txt acronyms.1.txt acronyms_dup.txt
	rm acronyms_sp.txt acronyms_directory.txt
	# @Warning: Duplicate have been process manually !
	# @todo:delete: Nantes, Montpellier, Toulouse, Secrétariat, Guangzhou, Fondatation
	# @todo:delete: CES, BUDGET, Sacem, CIO, Inee, CDC
	# @todo:add: CNI
	# ./script/acronyms_to_json.py

update_lexicon: acronyms institutions mfs_organizations
	python pyalbert/utils/acronyms_to_json.py
	pyalbert/utils/create_python_file.sh "# DO NOT EDIT" "INSTITUTIONS" _data/liste-mfs.json pyalbert/lexicon/institutions.py
	pyalbert/utils/create_python_file.sh "# DO NOT EDIT" "MFS_ORGANIZATIONS" _data/liste-mfs.json pyalbert/lexicon/mfs_organizations.py

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
	python3 pyalbert.py index experiences --index-type bm25
	python3 pyalbert.py index sheets --index-type bm25
	python3 pyalbert.py index chunks --index-type bm25
	python3 pyalbert.py index experiences --index-type e5
	python3 pyalbert.py index chunks --index-type e5

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
	# Show a doc payload
	# curl -X GET "http://localhost:9202/index_name/_doc/{doc_id}
	# 
	# qdrant
	curl -X GET "http://localhost:6333/collections" | jq 
	# count point in a collection
	# curl -X GET "http://localhost:6333/collections/{collection_name}"  | jq "{count:.result.points_count}"
	# Show a point payload
	# curl -X GET "http://localhost:6333/collections/{collection_name}/points/{point_id}" | jq ".result.payload"

OSC_PROFILE="default" # Usage: make list_vms OSC_PROFILE="cloudgouv"
VMID="i-3fcd96ff" # Usage: make get_vm VMID=i-bb5568c0
list_vms:
	@osc-cli api ReadVms --profile "$(OSC_PROFILE)" | jq ".Vms | .[] | { VmId, State, Tags }"

get_vm:
	@osc-cli api ReadVms --profile "$(OSC_PROFILE)" \
			--Filters "{\
			\"VmIds\": [\"$(VMID)\"],\
		}" | jq ".Vms | .[] | { VmId, State, Tags }"

start_vm:
	@osc-cli api StartVms --profile "$(OSC_PROFILE)" --VmIds "[\"$(VMID)\"]"

stop_vm:
	@read -p "Please confirm to STOP this VM ($(VMID))? (y/n) " answer;\
	answer=$$(echo $$answer | tr '[:upper:]' '[:lower:]'); \
	if [ "$$answer" = "y" ] || [ "$$answer" = "yes" ]; then \
			echo "You answered yes. Continuing..."; \
	else \
			echo "You answered no. Stopping..."; exit 1; \
	fi
	@osc-cli api StopVms --profile "$(OSC_PROFILE)" --VmIds "[\"$(VMID)\"]"

