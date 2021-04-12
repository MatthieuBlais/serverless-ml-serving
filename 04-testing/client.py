import requests
from jsonschema import validate
import boto3
import yaml
import os
from datetime import datetime

class APIClient():

    def __init__(self, host):
        self.host = host
        self.s3 = boto3.client('s3', region_name=os.environ["AWS_REGION"])
        self.report = {
            "details": {
                "start_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            },
            "cases": []
        }
        
    def run_tests(self, spec_bucket, spec_key):
        self.endpoints = self._download_endpoints(spec_bucket, spec_key)
        self.report["details"]["bucket"] = spec_bucket
        self.report["details"]["key"] = spec_key
        success = True
        for endpoint in self.endpoints:
            case = self.test_endpoint(endpoint)
            success = success and case["success"]
            self.report["cases"].append(case)
        self.report["details"]["end_date"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def test_endpoint(self, endpoint):
        results = []
        for idx, testcase in enumerate(endpoint.get("tests", [])):
            request = self._format_request(endpoint, testcase)
            assertions = self._format_assertions(endpoint, testcase.get("response", {}))
            req = self.call(**request)
            validity, report = ResponseValidation.validate(req, assertions)
            results.append({
                "endpoint": endpoint.get('endpoint'),
                'method': endpoint.get("method"),
                "test_id": idx,
                "success": validity,
                "details": report
            })
        return results

    def upload_report(self, bucket, key, report):
        self.s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(self.report)
        )

    def call(self, method, endpoint, headers={}, data=None):
        return requests.request(method, f"{self.host}{endpoint}", headers=headers, data=data)

    def _download_endpoints(self, bucket, key):
        """Download test set from S3"""
        obj = self.s3.get_object(Bucket=bucket, Key=key)
        return yaml.safe_load(obj["Body"].read())

    def _format_request(self, endpoint, testcase):
        return {
            'method': endpoint.get("method"), 
            'endpoint': endpoint.get('endpoint'),
            'headers': testcase.get('headers', endpoint.get("headers", {})),
            'data': testcase.get('data')
        }

    def _format_assertions(self, endpoint, assertion):
        return {
            'code': assertion.get("code", 200), 
            'headers': assertion.get('headers', {}),
            'schema': testcase.get('schema', endpoint.get("schema", None)),
            'body': testcase.get('body', None)
        }



class ResponseValidation:

    @classmethod
    def validate(cls, request, assertions):
        report = {
            "code": None,
            "headers": None,
            "schema": None,
            "body": None
        }
        success = True
        if assertions["code"]:
            code_validation = cls._response_code(request.status_code, assertions["code"])
            success = success and code_validation
            report["code"] = {
                "raw": request.status_code,
                "success": code_validation
            }
        if assertions["headers"]:
            headers_validation = cls._headers(request.headers, assertions["headers"])
            success = success and headers_validation
            report["headers"] = {
                "raw": request.headers,
                "success": headers_validation
            }
        if assertions["schema"]:
            schema_validation, err = cls._schemas(request.json(), assertions['schema'])
            success = success and schema_validation
            report["schema"] = {
                "raw": request.json(),
                "success": schema_validation,
            }
            if err:
                report["schema"]["details"] = err
        if assertions["body"]:
            body_validation = cls._body(request.json(), assertions['body'])
            success = success and body_validation
            report["schema"] = {
                "raw": request.json(),
                "success": body_validation
            }
        return success, report


    @classmethod
    def _headers(cls, headers, assertions):
        for key, value in assertions.items():
            if key not in 
            assert key in headers and headers[key] == value

    @classmethod
    def _response_code(cls, code, assertion):
        return code == assertion:

    @classmethod
    def _schemas(cls, body, assertion):
        try:
            validate(instance=body, schema=assertion)
            return True, None
        except Exception as e:
            return False, str(e)

    @classmethod
    def _body(cls, headers, body, assertion):
        if type(body) == 

        schema:
          dfsdf: sdfsdf
        assert:
          dfsdf: dsfsdf
        