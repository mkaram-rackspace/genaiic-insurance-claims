FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.11
# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

RUN yum install -y poppler-utils

# Copy function code
COPY . ${LAMBDA_TASK_ROOT}


# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "extract_attributes_llm_image.lambda_handler" ]
