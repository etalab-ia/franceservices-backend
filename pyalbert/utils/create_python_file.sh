#!/bin/bash

# Check if the correct number of arguments are provided
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <header> <variable_name> <json_file> <output_python_file>"
    exit 1
fi


header="$1"
variable_name="$2"
json_file="$3"
output_file="$4"

{
  echo -e "$header"
  echo ""
  echo ""
  echo "$variable_name = $(cat "$json_file")"
} > "$output_file"
