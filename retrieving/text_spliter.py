# Merci a Pierre-Louis Veyrenc pour son aide

"""
The default LangChain text splitters split either based on sentences (NLTKTextSplitter) or on token length (TokenTextSplitter).
We would like to base chunk sizes on token count, but never split in the middle of a sentence - a behaviour that TokenTextSplitter does exhibit.
The HybridSplitter class implements a custom splitter that combines both criteria.
"""
from typing import (
    Optional,
    Union,
    Literal,
    AbstractSet,
    Collection,
    Any,
    List,
    Callable,
)

from langchain.text_splitter import NLTKTextSplitter
from nltk import download
from nltk.tokenize import sent_tokenize

download("punkt", quiet=True)


def get_token_length_function(
    encoding_name: str = "gpt2",
    model_name: Optional[str] = None,
    allowed_special: Union[Literal["all"], AbstractSet[str]] = set(),
    disallowed_special: Union[Literal["all"], Collection[str]] = "all",
    *args,
    **kwargs,
) -> Callable[[str], int]:
    # Code taken from TextSplitter.from_tiktoken_encoder

    try:
        import tiktoken
    except ImportError:
        raise ValueError(
            "Could not import tiktoken python package. "
            "This is needed in order to calculate max_tokens_for_prompt. "
            "Please install it with `pip install tiktoken`."
        )

    if model_name is not None:
        enc = tiktoken.encoding_for_model(model_name)
    else:
        enc = tiktoken.get_encoding(encoding_name)

    def _tiktoken_encoder(text: str, **kwargs: Any) -> int:
        return len(
            enc.encode(
                text,
                allowed_special=allowed_special,
                disallowed_special=disallowed_special,
                **kwargs,
            )
        )

    return _tiktoken_encoder


def split_into_parts(input: str, n_parts: int = 1) -> list[str]:
    """
    Split the input text into n_parts approximately equally-sized parts along sentence borders (will never split in the middle of a sentence).
    """
    sentences = sent_tokenize(input, language="french")
    avg_length = len(input) // n_parts

    parts = []
    buffer = []
    i = 0
    for sen in sentences:
        if i > avg_length:
            parts.append(" ".join(buffer))
            buffer = []
            i = 0

        buffer.append(sen)
        i += len(sen)

    parts.append(" ".join(buffer))

    return parts


def split_along_markdown(input: str, max_splitting_depth: int = 1) -> list[str]:
    """
    Split the input text into parts following markdown heading, following a priority list: horizontal lines ***, then ---, then ___, then all heading levels.
    The max_splitting_depth argument tells the algorithm at what level of granularity to split.

    Ex: in a text containing ***,  ##, and #### separators, splitting with max_splitting_depth=2 will split the input twice (along *** and ##, but not ####).
    """
    separators = [
        # Horizontal lines
        "\n\n***\n\n",
        "\n\n---\n\n",
        "\n\n___\n\n",
        # Try to split along Markdown headings (starting with level 2)
        "\n## ",
        "\n### ",
        "\n#### ",
        "\n##### ",
        "\n###### ",
        # Note the alternative syntax for headings (below) is not handled here
    ]

    valid_separators = [sep for sep in separators if sep in input][:max_splitting_depth]

    parts = [input]
    # Try with each separator, recursively splitting along each of them.
    for sep in valid_separators:
        new_parts = []
        for part in parts:
            new_parts.extend(part.split(sep))
        parts = new_parts

    return parts


def split_along_md_or_parts(text: str, max_splitting_depth: int = 1, n_parts: int = 3):
    md_splits = split_along_markdown(text, max_splitting_depth=max_splitting_depth)

    if len(md_splits) == 1 and n_parts > 1:
        res = split_into_parts(text, n_parts=n_parts)
    else:
        res = md_splits

    return res


class HybridSplitter(NLTKTextSplitter):
    """
    Custom splitter that combines an NLTKTextSplitter and a token encoder (like TokenTextSplitter or the result of TextSplitter.from_tiktoken_encoder).
    Returns splits with a length based on token count rather than character count: returned splits will have less tokens than the specified chunk_size - as long as no one sentence exceeds the chunk_size - and will chunk_overlap based on tokens.
    However, the splits may be signficantly shorter than the requested size, in order to ensure we never split in the middle of a sentence.
    """

    def __init__(
        self,
        chunk_size: int = 4000,
        chunk_overlap: int = 200,
        length_function: Callable[
            [str], int
        ] = None,  # This argument should really not be overwritten
        separator: str = "\n\n",
        encoding_name: str = "gpt2",
        model_name: Optional[str] = None,
        allowed_special: Union[Literal["all"], AbstractSet[str]] = set(),
        disallowed_special: Union[Literal["all"], Collection[str]] = "all",
        **kwargs: Any,
    ):
        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator=separator,
            length_function=length_function
            or get_token_length_function(
                encoding_name=encoding_name,
                model_name=model_name,
                allowed_special=allowed_special,
                disallowed_special=disallowed_special,
                **kwargs,
            ),
            # We are obligated to use this kind of unwieldly ternary because the super() call needs to be the first statement
        )  # super().__init__() call to the parent NLTKTextSplitter class

    def split_text(self, text: str) -> List[str]:
        # When looking at the code for NTLKTextSplitter.split_text(), notice that self._tokenizer splits into individual sentences, then re-merges them into chunks.

        sentences = (
            sentence + ("" if sentence[-1] == " " else " ")
            for sentence in self._tokenizer(text)
        )
        # Add a space to the end of every sentence so that we don't transform 'Sen1. Sen2' into 'Sen1.Sen2' when merging
        # This is important if we want to re-use the NLTK splitter down the line, as it actually is sensitive to the presence of this space

        merges = [
            merge + ("" if merge[-1] == " " else " ")
            for merge in self._merge_splits(sentences, "")
        ]  # Same as above, also add spaces
        # Makes use of our custom length_function in _merge_splits
        return merges


class PartEnforceHybridSplitter(HybridSplitter):
    """
    Implements the same hybrid behaviour as its parent HybridSplitter, but first enforcing splits based on the given part_separator.
    The text is first split according to the part_separator, and then each part is split using the HybridSplitter - the final result is a flattened list of all the splits.
    Thus, this many return many splits buth they are all ensured to be smaller than the given chunk_size.
    """

    def __init__(self, part_separator: str = "\n ====== _-_ ===== \n", **kwargs: Any):
        super().__init__(
            **kwargs
        )  # super().__init__() call to the parent NLTKTextSplitter class
        self.part_separator = part_separator

    def split_text(self, text: str) -> List[str]:
        hybrid_split_function = super().split_text
        enforced_splits = text.split(self.part_separator)

        resulting_splits = []

        for part in enforced_splits:
            resulting_splits.extend(hybrid_split_function(part))

        return resulting_splits


if __name__ == "__main__":
    hs = HybridSplitter(chunk_size=1000, chunk_overlap=100)

    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer suscipit arcu sed condimentum porta. Quisque nec ex at odio pharetra porttitor eget vitae turpis. Phasellus malesuada fermentum tellus ac egestas. Sed vulputate convallis lectus varius auctor. Nulla sit amet dui nulla. Lorem ipsum dolor sit amet, consectetur adipiscing elit. In mollis, dui ut vulputate sodales, orci nisi varius erat, ut semper lacus lectus dapibus ex. Vivamus vestibulum condimentum libero, a dictum dolor fermentum non. Cras at ex facilisis magna ultricies pretium. Aenean in vehicula purus, non tincidunt leo. Suspendisse mollis orci a placerat rhoncus. Interdum et malesuada fames ac ante ipsum primis in faucibus. Nam euismod hendrerit arcu sit amet ultricies. Phasellus mollis finibus mauris. Curabitur non iaculis lectus, suscipit semper leo. Aliquam erat volutpat.Integer suscipit volutpat nibh nec luctus. Vestibulum vestibulum euismod consectetur. Phasellus id laoreet lorem. Vivamus rhoncus sapien non risus fermentum aliquet. Vivamus eu erat vehicula, consequat diam non, cursus lorem. Curabitur nec nisi dictum, ultrices dui vitae, lobortis nibh. Nulla sagittis tempus augue, non efficitur urna tempus id. Mauris tincidunt, enim quis varius varius, nulla dui tempor urna, non faucibus nunc magna quis mauris. Curabitur euismod neque at libero aliquet sagittis.Donec vitae ultrices nibh. In placerat et sem et iaculis. Nullam pharetra arcu et ante accumsan, non hendrerit arcu egestas. Sed sed auctor neque, vel iaculis metus. Interdum et malesuada fames ac ante ipsum primis in faucibus. Suspendisse potenti. Quisque ut velit sit amet tellus placerat volutpat eu at urna. Pellentesque rutrum, erat sit amet sagittis hendrerit, neque neque aliquam quam, et iaculis quam lorem et nisi. Etiam eu lobortis sapien. Morbi sagittis et est at placerat. Suspendisse in hendrerit turpis, quis bibendum turpis. Aliquam scelerisque turpis sit amet fringilla elementum. Phasellus porta maximus lorem, ut aliquam elit iaculis id. Fusce eu velit facilisis, condimentum nunc et, mattis nunc.Nulla facilisi. Proin id libero elit. Ut in iaculis felis, eget bibendum ex. Nullam vitae justo in orci vehicula semper. Nulla gravida urna non ipsum condimentum placerat. Quisque eget arcu urna. Pellentesque venenatis ullamcorper tortor, a varius nulla. Ut metus arcu, luctus id fermentum sit amet, sollicitudin sit amet libero. Sed facilisis egestas enim, id condimentum lorem consectetur eget. Nullam quis imperdiet massa. Sed vel bibendum nunc. Nam neque neque, sollicitudin imperdiet rutrum a, semper at dolor. Vestibulum ut tortor nisl. Donec suscipit felis ex, at vestibulum ipsum volutpat a.Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Suspendisse quis ex facilisis, molestie urna id, mollis urna. Donec porttitor sem eget diam pretium aliquet. Donec ac convallis massa. Pellentesque accumsan maximus diam. Phasellus gravida eu mauris eu aliquet. Nullam commodo ac lacus eget blandit. Praesent blandit leo neque, ac imperdiet risus suscipit ut. Sed non placerat sem. Interdum et malesuada fames ac ante ipsum primis in faucibus. Duis semper sit amet eros nec fringilla. Morbi a placerat diam, non interdum sem. Maecenas id ipsum non est sollicitudin auctor. Mauris non pharetra sapien.Quisque tortor ex, facilisis a ante eu, fringilla porttitor mi. Vestibulum sit amet iaculis orci, eu posuere ex. Integer arcu orci, tempor a tellus a, malesuada mollis nisi. Morbi euismod lobortis dolor, vitae sodales purus volutpat vel. Quisque orci lorem, egestas id nibh non, euismod ornare est. Phasellus non facilisis mi. Pellentesque scelerisque semper faucibus. Proin ac pretium tellus. Mauris imperdiet elit odio, quis pellentesque quam convallis vitae. Curabitur condimentum ligula vitae magna congue, at posuere leo lobortis. Etiam a augue ut eros consequat finibus. Vivamus sagittis molestie iaculis.Duis consequat quam at odio vulputate egestas. Cras urna libero, vehicula sed fermentum sit amet, suscipit quis sapien. Etiam pulvinar mauris quis sapien commodo, et semper quam scelerisque. Aliquam congue convallis augue, a aliquam urna euismod ac. Maecenas molestie orci magna, eget sodales ante auctor a. Phasellus maximus mollis elit. Etiam a nibh at est porta condimentum vitae sed nisi. Duis felis arcu, varius ac placerat in, egestas id lectus. Mauris sit amet elit scelerisque, dapibus libero id, pharetra ipsum.Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Pellentesque vulputate interdum justo, sit amet accumsan est eleifend id. Duis elit ligula, congue in malesuada tincidunt, imperdiet at velit. Suspendisse potenti. Duis imperdiet malesuada ultrices. Praesent blandit purus vel mauris placerat maximus. Vivamus in leo eget nulla consectetur cursus. Nullam id odio eu tellus rhoncus commodo. Quisque vel ultrices erat, in finibus tortor. Sed rutrum neque vitae ornare euismod. Nam egestas felis imperdiet diam ultrices laoreet. Aenean euismod ornare augue at ultrices. Nulla laoreet, lorem ut vehicula interdum, nibh leo mollis lorem, vel maximus dui metus ac ipsum. Curabitur pretium ligula ut tempor ullamcorper.Suspendisse potenti. Mauris luctus, ex non dictum vulputate, nulla dui fermentum purus, sed accumsan nunc nulla quis nunc. Aenean et magna dolor. Phasellus scelerisque non ipsum non pellentesque. Nulla aliquam id ex at dictum. Curabitur nec rhoncus sapien, ac scelerisque lacus. Phasellus hendrerit vulputate congue. Donec rutrum accumsan nibh, suscipit vehicula eros aliquam vitae. Aliquam quis molestie arcu. Proin commodo viverra massa sit amet commodo. Cras in massa vitae magna tincidunt luctus sed dapibus nulla. Duis nisi augue, condimentum et risus non, venenatis porttitor ante. Nam eget commodo dui. Fusce elementum nibh in volutpat aliquam.Integer quis mauris hendrerit, tincidunt urna nec, blandit velit. Aenean quam nunc, consectetur vel sollicitudin et, malesuada in ex. Curabitur ultricies metus ac mi tempor consequat. Nullam sapien risus, ultrices nec lacus nec, bibendum maximus enim. Maecenas porta orci sed pulvinar vestibulum. In ut mi nisi. Fusce arcu urna, gravida in orci tincidunt, auctor feugiat erat. Donec nisl velit, accumsan fringilla congue non, placerat vitae nunc. Etiam rutrum, nibh vitae pharetra auctor, tellus tortor rutrum arcu, venenatis cursus lectus sapien at massa. Integer lacinia diam nunc, ultricies finibus turpis vehicula id. Donec iaculis, nisl ac molestie bibendum, mi arcu lacinia risus, ac lacinia orci ligula sed arcu. Maecenas vitae velit non elit fermentum efficitur at a lacus. Aliquam erat volutpat. Fusce sit amet massa ac lectus condimentum pulvinar. Nam lectus est, bibendum nec libero eget, vehicula aliquam nibh. "

    splits = hs.split_text(text)
    for t in splits:
        print("=" * 30)
        print(f"Length {len(t)}, {hs._length_function(t)} tokens for chunk: \n '{t}'")
