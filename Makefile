
format_code:
	@# Format all python files
	pylsp.black --line-length 125 .

reorder_json_chunks:
	@# Reorder and clean the json database.
	# Usefull t compare different version of this file.
	cat ~/Downloads/files_as_chunks.json | jq 'sort_by(.metadata.xml_url) | map(del(.metadata.file))' > tmp.json

