# API

(work in progress)

### Fabrique LLM Routes

> **POST /api/fabrique**

Register configuration for "fabrique" text generation.

Headers:
```
Content-type: application/x-www-form-urlencoded  
```

Params:  
```
user_text(required): string : the user/civil experience to be answered
context: string : prompt information (need better doc @pclanglais ?)
institution: string : should be automatically added...
links: string : should be automatically added...
temperature: number between 0 and 1 : the orignalality of the answer (0: deterministic, 1: more creative)
```

Note: the answer result can then be obtained with `fabrique_stream`


> **GET /api/fabrique_stream**

Fabrique text answer generation.  
Server-sent stream like content.  
https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events


> **GET /api/fabrique_stop**

Stop a Fabrique text stream generation.

### Search Engines Routes

> **POST /api/search/{index}**

Search most relevant from a given {index}.

{index} can be:
- experiences: search the most relevant user experiences.
- sheets: search the most relevant sheets from service-public.fr.
- chunks: search the msot relevant chunks.

Headers:
```
Content-type: application/json
```

Params:  
```
q(required): string: search query
n(default=3): integer: max document to return
similarity(default=bm25) : string : similarity algorithm. Possible values : bm25, bucket, e5.
```

Returns: A Json list of result object ->  

For index=experiences:
```
{
    "title" : "Title of the experience",
    "description" : "The user experience",
    "intitule_typologie_1" : "where it comes from"
    "reponse_structure_1" : "see https://opendata.plus.transformation.gouv.fr/explore/dataset/export-expa-c-riences/information"
}
```

For index=sheets
```
{
    "title" : "Title of the sheet",
    "url" : "Url of the sheet",
    "introduction" : "Introduction of the sheet"
}
```

For index=chunks
```
{
    "title" : "Title of the sheet",
    "url" : "Url of the sheet",
    "introduction" : "Introduction of the sheet"
    "text" : "The text part of the sheet (the chunk)"
    "context" : "The context of the chunk (successive chapter/sub-chapter/situation titles if any)"
}
```
