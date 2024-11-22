from langchain import PromptTemplate


PROMPT_DEFAULT_HEADER = """Extract attributes from the attached document and remember to provide a valid JSON file in the following format:
<json>
{
  "Police Report Number": "",
  "Date of the incident": "",
  "Time of the incident": "",
  "Location of the incident": "",
  "Vehicle 1 (Guilty party) details": {
    "Driver's Name": "",
    "Vehicle Make and Model": "",
    "License Plate Number": "",
    "Insurance Information": "",
    "Description of the vehicle's condition": "",
    "Injuries sustained by the driver/passengers": ""
  },
  "Vehicle 2 (Victim party) details": {
    "Driver's Name": "",
    "Vehicle Make and Model": "",
    "License Plate Number": "",
    "Insurance Information": "",
    "Description of the vehicle's condition": "",
    "Injuries sustained by the driver/passengers": ""
  },
  "Description of the accident with relevant details": "",
  "Any third-party involvement (if applicable)": {
    "Name": "",
    "Description of injuries and/or damage": ""
  }
}
<json>
   

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


SYSTEM_PROMPT = """You are an AI assistant who is expert in extracting information from documents.
Carefully read the document given provided as a collection of images where each image is a document page.
Extract attributes listed below in <attributes></attributes> tags from the document.
The answer must contain the extracted attributes in JSON format. Do NOT include any other information in the answer.
If the attribute has multiple values, provide them as a list in this format: ["value1", "value2", "value3"].
If the attribute requires providing a description or free-form text, the value of the attribute must contain this text.
Note that some attributes are not directly stated in the document, but their values are implicitly defined in the text.
Do your best to extract a full value for each requested attribute from the document.
If provided, you must also follow the additional instructions in <instructions></instructions>.
Think step by step. First, summarize your thoughts in 2-3 sentences using <thinking></thinking> tags. Next, output the JSON in <json></json> tags. Do NOT include any other information in the answer. Remember that the response MUST be a valid JSON file.
 
"""


def load_prompt_template() -> PromptTemplate:
    """
    Creates LangChain prompt template

    Parameters
    ----------
    num_few_shots : int, by default 0
        Number of few shots to be included into the prompt
    instructions : str, by default ""
        Additional document-level instructions

    Returns
    -------
    PromptTemplate
        LangChain Prompt Template
    """

    # prepare input variables
    input_variables = ["document"]

    # prepare the prompt
    prompt = PROMPT_DEFAULT_HEADER




    return PromptTemplate(
        template=prompt,
        input_variables=input_variables,
    )
