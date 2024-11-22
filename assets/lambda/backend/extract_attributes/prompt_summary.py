"""
File content:
    Prompting utils
"""

from langchain import PromptTemplate
import re

PROMPT_DEFAULT_HEADER = """You are an AI assistant who is expert of processing car accident insurance claims. Carefully read the document given below in <document><json></json></document> tags in. Your task is analyzing the documents and extract valuable information to facilitate the claim process. Your goal is to provide a concise summary in JSON format, focusing on four main aspects: car owner information, aggregated car damage details, estimated part cost to fix the car damages and final summarization.

  1. **Car Owner Information**: Extract relevant details about the car ownerand car details, including their contact information and insurance policy details.
  2. **Aggregated Car Damage Parts**:Identify and summarize the damage to the vehicles involved in the accident from multiple photos. Aggregate the damage information from each photo into a unified summary, highlighting all affected parts and the extent of the damage.
  3. **Estimated Part cost**: Provide the estimated price of each parts and write final estimated cost for insurance claim will cover.
  3. **Final conclusion**: Provide a comprehensive conclusion of the accident, focusing on key factors such as the cause, severity, and any additional relevant details. Incorporate the aggregated damage information to present a unified overview of the damage sustained by the vehicles.
 
  Ensure that the extracted data is concentrated on car damage and evidence, omitting any unnecessary comments or information. Your summary should be clear, concise, and structured to facilitate a fair assessment of the accident and streamline the claims process.

  Document:
"""  

PROMPT_JSON_DOC = """
Document:
<document>
<json>
{json_doc_placeholder}
</json>
</document>
"""

PROMPT_JSON_OUTPUT = """
output:
"""


def load_prompt_template(event) -> PromptTemplate:
    """
    Creates LangChain prompt

    Parameters
    ----------
    event : json, 
        with output from extraction step lambda functions

    Returns
    -------
    PromptTemplate
        LangChain Prompt Template
    """

    # prepare the prompt
    prompt = PROMPT_DEFAULT_HEADER
    for doc in event['body']:
        if 'llm_answer' in doc: # the document is an audio file
            prompt += PROMPT_JSON_DOC.format(json_doc_placeholder=doc['llm_answer']['content'])
        if 'original_file_name' in doc and \
           re.search("\\.pdf$", doc['original_file_name']) and \
           re.search("\\.doc$", doc['original_file_name']) and \
           re.search("\\.docx$", doc['original_file_name']): # the document is a pdf, doc, or docx file
            # prompt += PROMPT_JSON_DOC.format(json_doc_placeholder=doc['attributes'])
            pass
        if 'original_file_name' in doc and \
           re.search("\\.png$", doc['original_file_name']) and \
           re.search("\\.jpg$", doc['original_file_name']) and \
           re.search("\\.jpeg$", doc['original_file_name']): # the document is a png, jpg, or jpeg file
            prompt += PROMPT_JSON_DOC.format(json_doc_placeholder=doc['raw_answer'])
        # if 'file_name' in doc.keys():
        #     if 'attributes' in doc.keys():
        #         prompt += PROMPT_JSON_DOC.format(json_doc_placeholder=doc['attributes'])

    return PromptTemplate(
        template=prompt,
        # input_variables=input_variables,
    )
