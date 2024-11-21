import base64
from io import BytesIO
from pdf2image import convert_from_path


def get_base64_encoded_images_from_pdf(pdf_file_path):
    images = convert_from_path(pdf_file_path)
    base64_img_strs = []
    for i, image in enumerate(images):
        buffered = BytesIO()

        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue())
        base64_string = img_str.decode('utf-8')
        base64_img_strs.append(base64_string)
    return base64_img_strs


def create_human_message_with_imgs(text, file=None, max_pages=20):
    content = []
    if file:
        if file.lower().endswith('.pdf'):
            base64_img_strs = get_base64_encoded_images_from_pdf(file)
        elif file.lower().endswith(".jpeg") or file.lower().endswith(".jpg") or file.lower().endswith(".png"):
            with open(file, "rb") as image_file:
                binary_data = image_file.read()
                base64_img_str = base64.b64encode(binary_data)
                base64_img_strs = [base64_img_str.decode('utf-8')]

        base64_img_strs = base64_img_strs[:max_pages]
        if not base64_img_strs:
            raise ValueError(
                'No images found in the file. Consider uploading a different file or adjust cutoff settings.')

        for base64_img_str in base64_img_strs:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": f"image/jpeg",
                        "data": base64_img_str,
                    },
                },
            )
    content.append({"type": "text", "text": text})
    return {'role': 'user', 'content': content}


def create_assistant_response(marking_file):
    with open(marking_file) as f:
        marking_text = f.read()
        content = [{
            "type": "text",
                    "text": marking_text
        }]
    return {'role': 'assistant', 'content': content}


# ============= FEW SHOTS LOGIC: yet to be added ============

# def get_end_pages_cut_client(client_id):
#     table = dynamodb.Table(CUSTOMER_ID_TABLE_NAME)
#     response = table.get_item(Key={"CustomerId": str(client_id).lower()})
#     item = response.get("Item")
#     return item["end_pages_to_cut"]


# def get_marked_example(prompt, client_id):
#     table = dynamodb.Table(CUSTOMER_ID_TABLE_NAME)
#     response = table.get_item(Key={"CustomerId": str(client_id).lower()})
#     item = response.get("Item")

#     if item:
#         LOGGER.info("Adding few shot examples")
#         pdf_file_key_s3 = item["pdf_path"]
#         marking_file_key_s3 = item["markings_path"]
#         # load marked example
#         # create directory for fewshot examples
#         os.makedirs(f"/tmp/fewshots/{MARKINGS_FOLDER}", exist_ok=True)
#         file_path = f"/tmp/fewshots/{pdf_file_key_s3}"
#         marking_file_path = f"/tmp/fewshots/{marking_file_key_s3}"

#         S3_CLIENT.download_file(BUCKET_NAME, pdf_file_key_s3, file_path)
#         S3_CLIENT.download_file(BUCKET_NAME, marking_file_key_s3, marking_file_path)

#         LOGGER.info(f"Downloaded marked example from s3://{BUCKET_NAME}/{pdf_file_key_s3}")

#     else:
#         LOGGER.error(f"Client with id {client_id} not found in the database")
#         return {"statusCode": 404, "body": "Client not found"}

#     messages = [create_human_message_with_imgs(prompt, file_path), create_assistant_response(marking_file_path)]
#     return messages
