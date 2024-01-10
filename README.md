# LIA - Legal Information Assistant

This project contains the source code of LIA: the **L**egal **I**nformation **A**ssistant, also known as Albert.
It is a conversational agent that uses official French data sources to answer the agent questions.


## PyAlbert

`pyalbert` is a CLI tool that help build the sources and the model needed for the API.

Once installed, the complete documentation can be view with the command:

    ./albert.py --help

The process to build the data, and their corresponding `pyalbert` subcommands (checked if integrated to the CLI) are summarized below

1. [x] fetching the French data corpus -- `pyalbert download`.
2. [x] pre-processing and formatting the data corpus -- `pyalbert make_chunks`.
3. [x] feed the <index/vector> search engines -- `pyalbert index`
3. [ ] fine-tuning the LLMs. Independents script located in the folder `finetuning/`.
4. [x] evaluating the models -- `pyalbert evaluate`.

**NOTE**: The step 3 hides a step which consists of building the embeddings from pieces of text (chunks). This step requires a GPU and can be achieves with the command `pyalbert make_embeddings`. This command will create the data required for vector indexes build with the option `pyalbert index --index-type e5`. You can see the [deploy section](/api/README.md#deploy) of the API Readme to see all the step involved in the build process.

### Install 

    pip install -r requirements.txt


## Albert APIs

The API is built upon multiple services :

* The LLM API (GPU intensive): This API is managed by vllm, and the executable is located in `api_vllm/`.
* A vector database (for semantic search), based on Qdrant.
* A search-engine (for full-text search), based on ElasticSearch.
* The main/exposed API: the app executable and configurations are located in the folder `api/`.

See the dedicated [Readme](/api/README.md) for more information about the API configuration, testing, and  **deployment**.


## Folder structure

- \_data/: contains volatile and large data downloaded by pyalbert.
- api/: the code of the main API.
- api_vllm/: the code of the vllm API.
- commons/: code shared by different modules, such as the Albert API client, and prompt encoder.
- corpus_generation/: **Independent** scripts to generate Q/a or evaluation data using third party service (Mistral, Openai etc)
- finetuning/: **Independent** fine-tuning scripts.
- sourcing/: code behind `pyalbert download ...` and `pyalbert make_chunks`.
- ir/: code behind `pyalbert index ...`
- evaluation/: code behind `pyalbert evaluate ...`
- scripts/: Various tests scripts, not integrated to pyalbert (yet).
- tests/: Various util scripts, not integrated to pyalbert (yet).
- contrib/: configuration files to deploy Albert.
- notebooks/: Various notebooks used for testing, evaluation demo or fine-tuning.
- docs/: documentation resources.
- wiki/: wiki resources.


## Contributing

TODO


## License

TODO


## Acknowledgements

TODO


