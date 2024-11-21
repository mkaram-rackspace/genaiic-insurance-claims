"""
Copyright 2024 Amazon.com, Inc. or its affiliates. All Rights Reserved.

This is AWS Content subject to the terms of the Customer Agreement
----------------------------------------------------------------------

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
from helpers import create_human_message_with_imgs
from langchain_core.messages import SystemMessage
from model.bedrock import create_bedrock_client
from model.params import BedrockParams, ModelSpecificParams
from model.parser import parse_json_string
from prompt import SYSTEM_PROMPT, load_prompt_template
from utils import filled_prompt  # token_count_tokenizer, truncate_document

LOGGER = logging.Logger("ENTITY-EXTRACTION-MULTIMODAL", level=logging.DEBUG)
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


def lambda_handler(event, context):
    """
    Lambda handler
    """

    LOGGER.debug(f"event: {event}")

    # parse event
    if "requestContext" in event:
        LOGGER.info("Received HTTP request.")
        body = json.loads(event["body"])
    else:  # step functions invocation
        body = event["body"]
    LOGGER.info(f"Received input: {body}")

    # get model ID and params
    GENERATOR_CONFIG["temperature"] = body["model_params"]["temperature"]
    model_id = body["model_params"]["model_id"]

    if model_id.split(".")[0] == "meta":
        GENERATOR_CONFIG["max_tokens"] = 2048

    file_key = body.get("file_name")
    client_id = body.get("client_id")
    # prompt = body.get("prompt", PROMPT)
    # system_prompt = body.get("system_prompt", SYSTEM_PROMPT)
    # get fixed model params
    model_id = body["model_params"]["model_id"]

    # import Bedrock model class
    if model_id.startswith("cohere") or model_id.startswith("ai21"):
        from langchain_community.llms.bedrock import Bedrock
    else:
        from langchain_community.chat_models import BedrockChat as Bedrock

    fixed_params = {"STOP_WORDS": ["\n\nuser:"], "TOP_P": 0.95}

    # load variable model params

    model_params = ModelSpecificParams(
        model_id=model_id,
        params=BedrockParams(
            max_tokens=body["model_params"].get("answer_length", 1024),
            stop_sequences=fixed_params["STOP_WORDS"],
            temperature=body["model_params"]["temperature"],
            top_p=fixed_params["TOP_P"],
        ),
    )

    LOGGER.info(f"MODEL_PARAMS: {model_params.to_dict()}")

    prompt_template = load_prompt_template()
    LOGGER.info(f"Prompt template: {prompt_template}")

    filled_template = filled_prompt(
        template=prompt_template.template,
    )

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    LOGGER.info("Using Bedrock LLM.")
    llm = Bedrock(
        client=BEDROCK_CLIENT,
        model_id=model_id,
        model_kwargs=model_params.to_dict(),
        streaming=True if not model_id.startswith("ai21") else False,
    )

    # load file to local lambda storage if s3_location is given:
    if file_key:
        file_key_s3 = file_key
        ending = file_key_s3.split(".")[-1]
        S3_CLIENT.download_file(S3_BUCKET, file_key_s3, f"/tmp/file.{ending}")
        file = f"/tmp/file.{ending}"
        LOGGER.info(f"Downloaded file to /tmp/file.{ending}")

    # ============= FEW SHOTS LOGIC: yet to be added ============
    # if client_id:
    #     LOGGER.info("Adding few-shot example for the client_id")
    #     # get a pair of messages: user message - assistant response
    #     # farmusol
    #     example_messages = get_marked_example(prompt, client_id)
    #     end_pages_to_cut = get_end_pages_cut_client(client_id)
    #     messages.extend(example_messages)

    # read example
    human_message = create_human_message_with_imgs(filled_template, file, max_pages=20)
    messages.append(human_message)
    LOGGER.info("Calling LLM")
    response = llm.invoke(messages)

    try:
        response_json = parse_json_string(response.content)
    except Exception as e:
        LOGGER.debug(f"Error parsing response: {e}")
        response_json = {}
    LOGGER.info(f"Parsed response: {response_json}")

    json_data = json.dumps(
        {
            "answer": response_json,
            "raw_answer": response.content,
            "file_key": body["file_name"],
            "original_file_name": body["file_name"],
        }
    )

    S3_CLIENT.put_object(
        Body=json_data,
        Bucket=S3_BUCKET,
        Key=f"{PREFIX_ATTRIBUTES}/{body['file_name'].split('/', 1)[-1].removesuffix('.txt')}.json",
        ContentType="application/json",
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json_data,
    }
