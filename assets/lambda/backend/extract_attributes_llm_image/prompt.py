from langchain import PromptTemplate


PROMPT_DEFAULT_HEADER = """Extract attributes from the attached images and remember to provide a valid JSON file in the following example format:
<json>
"Headlights": {
    "severity_of_damage": "Severe",
    "nature_of_damage": "Collision",
    "description_of_damage": "Both headlights are shattered and non-functional, indicating a high-impact collision."
    },
"Windshield": {
    "severity_of_damage": "Moderate",
    "nature_of_damage": "Debris",
    "description_of_damage": "The windshield has a large crack caused by flying debris."
    }
</json>
"""


PROMPT_DEFAULT_TAIL = """
Attributes to be extracted:
<attributes>
{attributes}
</attributes>

<document_level_instructions_placeholder>

Output:"""


PROMPT_FEW_SHOT = """<example>
<document_text_extracted_from_images>
{few_shot_input_placeholder}
</document_text_extracted_from_images>

Attributes to be extracted:
<attributes>
{{attributes}}
</attributes>

<document_level_instructions_placeholder>

Output:
{few_shot_output_placeholder}
</example>

"""

PROMPT_INSTRUCTIONS = """You must follow these additional instructions:
<instructions>
{instructions}
</instructions>
"""


SYSTEM_PROMPT = """You are an AI assistant who is expert in filed of car accident insurance claim company.
            Your task is to analyze the photos to gather clues and information related to the accident.
            Look closely at the images and identify any visible damage to vehicles, road conditions, weather conditions,
            traffic signs, or any other relevant details that can help assess the cause and severity of the accident.
            Pay attention to details such as the position of vehicles, skid marks, debris,
            and any other visible evidence that could provide insights into how the accident occurred.
            Your goal is to extract valuable information from the photos to facilitate the claims process and ensure a fair assessment of the accident.
Extract attributes listed below in <attributes></attributes> tags from the image.
The answer must contain the extracted attributes in JSON format. Do NOT include any other information in the answer.
If the attribute has multiple values, provide them as a list in this format: ["value1", "value2", "value3"].
If the attribute requires providing a description or free-form text, the value of the attribute must contain this text.
If provided, you must also follow the additional instructions in <instructions></instructions>.
Think step by step. First, summarize your thoughts in 2-3 sentences using <thinking></thinking> tags. Next, output the JSON in <json></json> tags. Do NOT include any other information in the answer. Remember that the response MUST be a valid JSON file.

example output format:

"""


def load_prompt_template() -> PromptTemplate:
    """
    Creates LangChain prompt template

    Returns
    -------
    PromptTemplate
        LangChain Prompt Template
    """

    # prepare input variables
    input_variables = ["document"]
    # for i in range(num_few_shots):
    #     input_variables += [f"few_shot_input_{i}", f"few_shot_output_{i}"]

    # prepare the prompt
    prompt = PROMPT_DEFAULT_HEADER
    # for i in range(num_few_shots):
    #     prompt += PROMPT_FEW_SHOT.format(
    #         few_shot_input_placeholder="{" + f"few_shot_input_{i}" + "}",
    #         few_shot_output_placeholder="{" + f"few_shot_output_{i}" + "}",
        # )
    # prompt += PROMPT_DEFAULT_TAIL

    # add instructions
    # if instructions.strip():
    #     prompt = prompt.replace(
    #         "<document_level_instructions_placeholder>",
    #         PROMPT_INSTRUCTIONS,
    #     )
    #     input_variables += "instructions"
    # else:
    #     prompt = prompt.replace(
    #         "\n<document_level_instructions_placeholder>\n", "\n")

    return PromptTemplate(
        template=prompt,
        input_variables=input_variables,
    )
