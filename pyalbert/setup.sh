#!/bin/bash

#|##################################################
#|Setup Albert from scratch
#|##################################################

# Fetch and parse corpuses
pyalbert create_whitelist
pyalbert download_rag_sources
pyalbert make_chunks --structured
# Feed the search eninges
pyalbert index experiences --index-type bm25
pyalbert index sheets      --index-type bm25
pyalbert index chunks      --index-type bm25
pyalbert index experiences --index-type e5
pyalbert index chunks      --index-type e5

# Launch albert api on localhost (test)
pyalbert serve
