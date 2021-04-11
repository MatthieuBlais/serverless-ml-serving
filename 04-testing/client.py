import requests
from jsonschema import validate
import boto3
import yaml

class APIClient():

    def __init__(self, host, spec_bucket, spec_key):
        self.host = host
        self.s3 = boto3.client('s3', region_name=os.environ["AWS_REGION"])
        self.endpoints = self._download_endpoints(spec_bucket, spec_key)

    def run_tests(self):
        for endpoint in self.endpoints:
            req = self.call(endpoint['method'], endpoint['method'])

    def test_endpoint(self, endpoint):
        for testcase in endpoint.get("tests", []):
            req = self.call(
                testcase.get('method', endpoint.get("method")), 
                endpoint.get('endpoint'),
                testcase.get('headers', endpoint.get("headers")),
                testcase.get('data')
            )
            req_validity = ResponseValidation.validate(req, testcase.get('response'))

            

    def call(self, method, endpoint, headers={}, data=None):
        return requests.request(method, f"{self.host}{endpoint}", headers=headers, data=data)

    def _download_endpoints(self, bucket, key):
        """Download test set from S3"""
        obj = self.s3.get_object(Bucket=bucket, Key=key)
        return yaml.safe_load(obj["Body"].read())



class ResponseValidation:

    @classmethod
    def validate(cls, request, assertions):
        if "code" in assertions:
            cls._response_code(request.status_code, assertions["code"])
        cls._response_code()
        if "headers" in assertions:
            headers = assertions["headers"]
            cls._headers(request.headers, headers)
        if "schema" in assertions:
            cls._schemas(request.json(), assertions['schema'])
        if "body" in assertions:
            cls._body(request.headers, request.text, assertions['body'])


    @classmethod
    def _headers(cls, headers, assertions):
        for key, value in assertions.items():
            assert key in headers and headers[key] == value

    @classmethod
    def _response_code(cls, code, assertion):
        assert code == assertion

    @classmethod
    def _schemas(cls, body, assertion):
        validate(instance=body, schema=assertion)

    @classmethod
    def _body(cls, headers, body, assertion):
        if type(body) == 

        schema:
          dfsdf: sdfsdf
        assert:
          dfsdf: dsfsdf
        