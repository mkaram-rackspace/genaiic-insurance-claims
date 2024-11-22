"""
Helper classes for LLM inference
"""

from __future__ import annotations

import datetime
import json
import os
import time

import boto3
import requests
import streamlit as st

import logging
import sys
import re

API_URI = os.environ.get("API_URI")
STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN")

REQUEST_TIMEOUT = 900

LOGGER = logging.Logger("Streamlit::API", level=logging.DEBUG)
HANDLER = logging.StreamHandler(sys.stdout)
HANDLER.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
LOGGER.addHandler(HANDLER)

def invoke_step_function(
    file_keys: list[str],
    attributes: list[dict],
    instructions: str = "",
    few_shots: list[dict] = [],
    model_id: str = "anthropic.claude-v2:1",
    parsing_mode: str = "Amazon Textract",
    temperature: float = 0.0,
) -> str:
    """
    Invoke "attributes" via a step function boto3 call

    Parameters
    ----------
    file_keys : list[str]
        S3 keys for input documents
    attributes : list[dict]
        List of attribute dictionaries to be extracted
    instructions : str
        Optional high-level instructions, by default ""
    few_shots: list[dict]
        Optional list of few shot examples (input and output pairs)
    model_id : str, optional
        ID of the language model, by default "anthropic.claude-v2.1"
    parsing_mode : str, optional
        Parsing algorithm to use, by default "Amazon Textract"
    temperature : float, optional
        Model inference temperature, by default 0.0
    """

    client = boto3.client("stepfunctions")

    data = json.dumps(
        {
            "documents": file_keys,
            "attributes": attributes,
            "instructions": instructions,
            "few_shots": few_shots,
            "parsing_mode": parsing_mode,
            "model_params": {
                "model_id": model_id,
                "temperature": temperature,
            },
        }
    )

    response = client.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        input=data,
    )
    execution_arn = response["executionArn"]

    while True:
        time.sleep(int(1))

        response = client.describe_execution(executionArn=execution_arn)
        status = response["status"]
        print(f"Status: {status}")

        if status == "FAILED":
            break

        if status == "SUCCEEDED":
            output = json.loads(response["output"])

            groups = re.search("([\\s\\S]*?)<json>([\\s\\S]*?)</json>([\\s\\S]*?)", output["llm_answer"]["raw_answer"])
            accident_info=json.loads(groups[2])

            parsed_response_list = [{
                    "Key": "Car Owner",
                    "Value": accident_info["carOwnerName"]
                }, {
                    "Key": "Insurance Policy",
                    "Value": accident_info["carOwnerInsurancePolicy"]
                }, {
                    "Key": "Damage Details",
                    "Value": accident_info["damageDetails"]
                }, {
                    "Key": "Estimated Repair Cost",
                    "Value": accident_info["estimatedRepairCost"]
                }, {
                    "Key": "Final Claim Summary",
                    "Value": accident_info["finalClaimSummary"]
                }
                
            ]
            st.session_state["parsed_response"].extend(parsed_response_list)
            # parsed_response = {
            #     "Summary" : output["llm_answer"]["raw_answer"]
            # }
            # st.session_state["parsed_response"].append(parsed_response)




            st.session_state["raw_response"].append(output["llm_answer"]["raw_answer"])
            # for output in outputs:
            #     LOGGER.info(f"output: {output}")
            #     # llm_answer = output["llm_answer"]
            #     # LOGGER.info(f"llm_answer: {llm_answer}")
            #     # raw_answer = output["llm_answer"]["raw_answer"]
            #     # LOGGER.info(f"raw_answer: {raw_answer}")
            #     parsed_response = {
            #         "Summary" : output # ["llm_answer"]["raw_answer"]
            #     } # output["llm_answer"]["answer"]
            #     parsed_response["_file_name"] = output #["llm_answer"]["raw_answer"] # output["llm_answer"]["original_file_name"].split("/", 1)[-1]
            #     st.session_state["parsed_response"].append(parsed_response)
            #     st.session_state["raw_response"].append(output) #["llm_answer"]["raw_answer"])
            break


def invoke_file_upload(
    file,
    access_token: str,
) -> str:
    """
    Get presigned URL via API Gateway and upload the file to S3

    Parameters
    ----------
    file : _type_
        Streamlit uploaded file or string
    access_token : str
        Access token

    Returns
    -------
    str
        URL generation status message
    """

    if isinstance(file, str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        file_name = f"document_{timestamp}.txt"
    else:
        file_name = file.name

    params = {"file_name": file_name}

    response = requests.post(
        url=API_URI + "/url",
        json=params,
        stream=False,
        headers={"Authorization": access_token},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    response = response.json()

    files = {"file": file}

    if "post" in response:
        post_response = requests.post(
            url=response["post"]["url"],
            data=response["post"]["fields"],
            files=files,
            timeout=REQUEST_TIMEOUT,
        )
        post_response.raise_for_status()

    return response["post"]["fields"]["key"]
