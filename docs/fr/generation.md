# Stratégies de génération

La méthode `generate()` de HuggingFace permet plusieurs stratégies de génération résumées comme suit :

- **greedy decoding**  en appelant `greedy_search()` si `num_beams=1` et `do_sample=False`
- **contrastive search** en appelant `recherchecontrastive()` si `pénalité_alpha>0` et `top_k>1`
- **beam-search decoding** en appelant `beam_search()` si `num_beams>1` et `do_sample=False`
- **diverse beam-search decoding** en appelant `group_beam_search()`, si `num_beams>1` et `num_beam_groups>1`
- **constrained beam-search** en appelant `constrained_beam_search()`, si `constraints!=None` ou `force_words_ids!=None`
- **multinomial sampling** en appelant `sample()` si `num_beams=1` et `do_sample=True`
- **beam-search multinomial sampling** en appelant `beam_sample()` si `num_beams>1` et `do_sample=True`

Ressources :

- https://huggingface.co/docs/transformers/v4.31.0/en/main_classes/text_generation
- https://huggingface.co/docs/transformers/v4.31.0/en/generation_strategies
