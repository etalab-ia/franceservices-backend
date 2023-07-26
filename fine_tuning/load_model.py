from transformers import AutoModelForCausalLM
from peft import LoraConfig, PeftModel, get_peft_model
import torch
from .params import CHECKPOINT


def print_trainable_parameters(model):
    """
    Prints the number of trainable parameters in the model.
    """
    trainable_params = 0
    all_param = 0
    for _, param in model.named_parameters():
        all_param += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()
    print(
        f"trainable params: {trainable_params} || "
        f"all params: {all_param} || "
        f"trainable%: {100 * trainable_params / all_param}"
    )


def load_model() -> PeftModel:
    config = LoraConfig(
        r=16,
        lora_alpha=32,
        # target query and value projection layers for the adapter
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = AutoModelForCausalLM.from_pretrained(
        CHECKPOINT,
        load_in_8bit=True,
        device_map="auto",
    )

    for param in model.parameters():
        param.requires_grad = False  # freeze the model - train adapters later
        if param.ndim == 1:
            # cast the small parameters (e.g. layernorm) to fp32 for stability
            param.data = param.data.to(torch.float32)  # pylint: disable=no-member

    model.gradient_checkpointing_enable()  # reduce number of stored activations
    model.enable_input_require_grads()

    class CastOutputToFloat(torch.nn.Sequential):
        def forward(self, vector):  # pylint: disable=arguments-renamed
            return super().forward(vector).to(torch.float32)  # pylint: disable=no-member

    model.lm_head = CastOutputToFloat(model.lm_head)

    model = get_peft_model(model, config)
    print_trainable_parameters(model)

    return model
