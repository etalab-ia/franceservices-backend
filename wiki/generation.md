

The generate() method of huggingface allows several generation strategies summarized as follows:

- **greedy decoding** by calling greedy_search() if num_beams=1 and do_sample=False
- **contrastive search** by calling contrastive_search() if penalty_alpha>0 and top_k>1
- **beam-search decoding** by calling beam_search() if num_beams>1 and do_sample=False
- **diverse beam-search decoding** by calling group_beam_search(), if num_beams>1 and num_beam_groups>1
- **constrained beam-search** decoding by calling constrained_beam_search(), if constraints!=None or force_words_ids!=None

- **multinomial sampling** by calling sample() if num_beams=1 and do_sample=True
- **beam-search multinomial sampling** by calling beam_sample() if num_beams>1 and do_sample=True

Ressources:

- https://huggingface.co/docs/transformers/v4.31.0/en/main_classes/text_generation
- https://huggingface.co/docs/transformers/v4.31.0/en/generation_strategies
