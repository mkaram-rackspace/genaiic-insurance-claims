"""
Copyright © Amazon.com and Affiliates
This code is being licensed under the terms of the Amazon Software License available at https://aws.amazon.com/asl/
----------------------------------------------------------------------
File content:
    Lambda for extracting features from texts
"""

#########################
#   LIBRARIES & LOGGER
#########################

import json
import logging
import os
import sys

import boto3
from botocore.config import Config
from langchain import LLMChain
from langchain_aws import ChatBedrock
from model.bedrock import create_bedrock_client, get_model_params
from model.parser import parse_json_string
from prompt_summary import load_prompt_template
from utils import filled_prompt, token_count_tokenizer, truncate_document

LOGGER = logging.Logger("ENTITY-EXTRACTION", level=logging.DEBUG)
HANDLER = logging.StreamHandler(sys.stdout)
HANDLER.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
LOGGER.addHandler(HANDLER)


#########################
#       CONSTANTS
#########################

MAX_DOC_LENGTH_DIC = {
    "anthropic.claude-3-opus-20240229-v1:0": 200_000,
    "anthropic.claude-3-sonnet-20240229-v1:0": 200_000,
    "anthropic.claude-3-haiku-20240307-v1:0": 200_000,
    "anthropic.claude-v2:1": 200_000,
    "anthropic.claude-v2": 100_000,
    "anthropic.claude-instant-v1": 100_000,
    "mistral.mistral-large-2402-v1:0": 32_000,
    "mistral.mixtral-8x7b-instruct-v0:1": 32_000,
    "mistral.mistral-7b-instruct-v0:2": 32_000,
    "amazon.titan-text-premier-v1:0": 32_000,
    "amazon.titan-text-express-v1": 8_000,
    "amazon.titan-text-lite-v1": 4_000,
    "meta.llama3-70b-instruct-v1:0": 8_000,
    "meta.llama3-8b-instruct-v1:0": 8_000,
    "meta.llama2-70b-chat-v1": 4_096,
    "meta.llama2-13b-chat-v1": 4_096,
    "cohere.command-r-plus-v1:0": 128_000,
    "cohere.command-r-v1:0": 128_000,
    "cohere.command-text-v14": 4_000,
    "cohere.command-light-text-v14": 4_000,
    "ai21.j2-ultra-v1": 8_191,
    "ai21.j2-mid-v1,": 8_191,
}

GENERATOR_CONFIG = {
    "top_p": 1,  # cumulative probability of sampled tokens
    "top_k": 50,  # number of the top most probable tokens to sample
    "stop_words": [],  # words after which the generation is stopped
    "max_tokens": 4_096,  # max tokens to be generated
}

BEDROCK_REGION = os.environ["BEDROCK_REGION"]
BEDROCK_CONFIG = Config(connect_timeout=120, read_timeout=120, retries={"max_attempts": 5})
BEDROCK_CLIENT = create_bedrock_client(BEDROCK_REGION, BEDROCK_CONFIG)

S3_BUCKET = os.environ["BUCKET_NAME"]
S3_CLIENT = boto3.client("s3")

PREFIX_ATTRIBUTES = "attributes"


#########################
#        HANDLER
#########################


def lambda_handler(event, context):  # noqa: C901
    """
    Lambda handler
    """

    LOGGER.debug(f"event: {event}")

    # get model ID and params
    GENERATOR_CONFIG["temperature"] = 0
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

    if model_id.split(".")[0] == "meta":
        GENERATOR_CONFIG["max_tokens"] = 2048

    model_params = get_model_params(model_id=model_id, params=GENERATOR_CONFIG)
    LOGGER.info(f"LLM parameters: {model_id}; {model_params}")

    # set up LLM
    llm = ChatBedrock(
        client=BEDROCK_CLIENT,
        model_id=model_id,
        model_kwargs=model_params,
    )

    # prepare prompt template
    prompt_template = load_prompt_template(event)
    LOGGER.info(f"Prompt: {prompt_template}")

    # run entity extraction
    LOGGER.info(f"Calling the LLM {model_id} to extract attributes...")
    llm_chain = LLMChain(llm=llm, prompt=prompt_template, verbose=False)
    prompt_variables = {
        "request": "Summarize the car accident with a narrative",
    }
    response = llm_chain.invoke(prompt_variables)
    LOGGER.info(f"LLM response: {response}")

    # parse response
    try:
        response_json = parse_json_string(response["text"])
    except Exception as e:
        LOGGER.debug(f"Error parsing response: {e}")
        response_json = {}
    LOGGER.info(f"Parsed response: {response_json}")

    json_data = json.dumps(
        {
            "answer": response_json,
            "raw_answer": response["text"]
        }
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json_data,
    }
