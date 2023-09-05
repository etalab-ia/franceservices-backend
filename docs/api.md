# Routes

(work in progress)

**POST api/fabrique**

Register configuration for "fabrique" text generation.

Content-type: application/x-www-form-urlencoded
Params:
```
user_text(required): string : the user/civil experience to be answered
context: string : prompt information (need better doc @pclanglais ?)
institution: string : should be automatically added...
links: string : should be automatically added...
temperature: number between 0 and 1 : the orignalality of the answer (0: deterministic, 1: more creative)
```

Note: the answer result can then be obtained with `fabrique_stream`


**GET api/fabrique_stream**

Fabrique text answer generation.
Server-sent stream like content.
https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events


**GET api/fabrique_stop**

Stop a Fabrique text stream generation.

