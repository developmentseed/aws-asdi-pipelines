import json
import os

import requests
from aws_lambda_powertools.utilities.data_classes import SQSEvent, event_source
from stactools.core import use_fsspec
from stactools.noaa_cdr.stac import create_item

from aws_asdi_pipelines.cognito.utils import get_token


@event_source(data_class=SQSEvent)
def handler(event: SQSEvent, context):
    domain = os.environ["DOMAIN"]
    client_secret = os.environ["CLIENT_SECRET"]
    client_id = os.environ["CLIENT_ID"]
    scope = os.environ["SCOPE"]
    ingestor_url = os.environ["INGESTOR_URL"]
    token = get_token(
        domain=domain, client_secret=client_secret, client_id=client_id, scope=scope
    )
    headers = {"Authorization": f"bearer {token}"}
    use_fsspec()
    for record in event.records:
        record_body = json.loads(record.body)
        record_message = json.loads(record_body["Message"])
        for sns_record in record_message["Records"]:
            key = sns_record["s3"]["object"]["key"]
            path = f"s3://noaa-cdr-sea-surface-temp-optimum-interpolation-pds/{key}"
            print(path)
            stac = create_item(href=path)

            stac.collection_id = "noaa-oisst"
            response = requests.post(
                url=ingestor_url, data=json.dumps(stac.to_dict()), headers=headers
            )
            try:
                response.raise_for_status()
            except Exception:
                print(response.text)
                raise
