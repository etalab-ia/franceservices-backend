#!/bin/bash

python3 pyalbert download_rag_sources --storage-dir _data/
python3 pyalbert make_chunks --structured --storage-dir _data/
python3 pyalbert index experiences --index-type bm25 --recreate --storage-dir _data/
python3 pyalbert index sheets --index-type bm25 --recreate --storage-dir _data/
python3 pyalbert index chunks --index-type bm25 --recreate --storage-dir _data/
python3 pyalbert index experiences --index-type e5 --recreate --storage-dir _data/
python3 pyalbert index chunks --index-type e5 --recreate --storage-dir _data/

