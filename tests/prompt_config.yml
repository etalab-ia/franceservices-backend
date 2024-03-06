#!/bin/python

import sys
import os
from jinja2 import Environment, FileSystemLoader, meta
import yaml


sys.path.append(".")
os.chdir(os.path.dirname(os.path.abspath(__file__)))


if __name__ == "__main__":

    with open('prompt_config.yml') as f:
        config = yaml.safe_load(f)

    print("prompt format:", config.get("prompt_format"))
    print(config)
    print()
    for prompt in config["prompts"]:
        print(f'--- prompt mode: {prompt["mode"]} ---')
        env = Environment(loader=FileSystemLoader("."))
        template = env.get_template(prompt["template"])

        source = template.environment.loader.get_source(template.environment, template.name)
        variables = meta.find_undeclared_variables(env.parse(source[0]))
        print("variables:", variables)
        print("---")

        data = {
            "query": "Comment est votre blanquette ?",
            "chunks" : [
                {
                    "url": "http://data.gouv.fr",
                    "title": "A chunk title",
                    "text": "text texs\ntext again ",
                },
                {
                    "url": "http://...",
                    "title": "A chunk title",
                    "text": "text texs\ntext again ",
                    "context": "I > am > a > context"
                },

            ]
        }
        rendered_template = template.render(**data)
        print(rendered_template)
        print("---")
