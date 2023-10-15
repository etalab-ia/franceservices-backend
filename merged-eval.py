import json
import os

# @TODO: move this to the gpt, like for example: gpt evaluate name1 name2... --merge

names = ["albert-light-rag-v0", "albert-light-simple-v0"]
result = []

for i, name in enumerate(names):
    prompt_path = f"_data/p/{name}"
    answer_path = f"_data/x/{name}"

    prompt_files = os.listdir(prompt_path)
    answer_files = os.listdir(answer_path)

    for j, file in enumerate(prompt_files):
        prompt_file_path = os.path.join(prompt_path, file)
        answer_file_path = os.path.join(answer_path, file)

        with open(prompt_file_path, "r") as prompt_file, open(answer_file_path, "r") as answer_file:
            prompt_content = prompt_file.read()
            answer_content = answer_file.read()

            if i == 0:
                result.append({f"prompt_{name}": prompt_content, f"answer_{name}": answer_content})
            else:
                item = result[j]
                item.update({f"prompt_{name}": prompt_content, f"answer_{name}": answer_content})
                result.insert(j, item)


with open("albert-light-v0_eval.json", "w") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
