import requests
from jsonschema import validate
import boto3
import yaml
import os
from datetime import datetime
import json

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
        # self.endpoints = self._download_endpoints(spec_bucket, spec_key)
        self.endpoints = yaml.safe_load(open("definition.yaml").read())
        self.report["details"]["bucket"] = spec_bucket
        self.report["details"]["key"] = spec_key
        success_counter = 0
        for endpoint in self.endpoints:
            case, valid = self.test_endpoint(endpoint)
            success_counter += 1 if valid else 0
            self.report["cases"].append(case)
        success_rate = float(success_counter*100.0)/float(len(self.endpoints))
        self.report["details"]["end_date"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.report["details"]["success"] = success_rate == 100.0
        self.report["details"]["success_rate"] = success_rate

    def test_endpoint(self, endpoint):
        results = []
        success = True
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
                "details": report,
                "curl": self._get_curl(req)
            })
            success = success and validity
        return results, success

    def upload_report(self, bucket, key):
        print(json.dumps(self.report, indent=4))
        # self.s3.put_object(
        #     Bucket=bucket,
        #     Key=key,
        #     Body=json.dumps(self.report)
        # )

    def call(self, method, endpoint, headers={}, data=None):
        print(headers, data)
        return requests.request(method, f"{self.host}{endpoint}", headers=headers, data=json.dumps(data))

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
            'schema': assertion.get('schema', endpoint.get("schema", None)),
            'body': assertion.get('body', None)
        }

    def _get_curl(self, response):
        req = response.request
        command = "curl -X {method} -H {headers} -d '{data}' '{uri}'"
        method = req.method
        uri = req.url
        data = req.body
        headers = ['"{0}: {1}"'.format(k, v) for k, v in req.headers.items()]
        headers = " -H ".join(headers)
        return command.format(method=method, headers=headers, data=data, uri=uri)




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
            headers_validation, err = cls._headers(request.headers, assertions["headers"])
            success = success and headers_validation
            report["headers"] = {
                "raw": dict(request.headers),
                "success": headers_validation
            }
            if err:
                report["schema"]["details"] = err
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
            body_validation, err = cls._body(request.json(), assertions['body'])
            success = success and body_validation
            report["body"] = {
                "raw": request.json(),
                "success": body_validation
            }
            if err:
                report["body"]["details"] = err
        return success, report


    @classmethod
    def _headers(cls, headers, assertions):
        for key, value in assertions.items():
            if key not in headers:
                return False, f"Headers {key} is missing"
            if headers[key] != value:
                return False, f"Unexpected value for header {key}: {value}"
        return True, None

    @classmethod
    def _response_code(cls, code, assertion):
        return code == assertion

    @classmethod
    def _schemas(cls, body, assertion):
        try:
            validate(instance=body, schema=assertion)
            return True, None
        except Exception as e:
            return False, str(e)

    @classmethod
    def _body(cls, body, assertion):
        for key, value in assertion.items():
            if key not in body:
                return False, f"{key} is missing"
            if isinstance(value, dict):
                valid, err = cls._body(body[key], assertion[key])
                if not valid:
                    return False, err
            elif isinstance(value, list):
                for val in value:
                    valid, err = cls._body(body[key], assertion[key])
                    if not valid:
                        return False, err
            else:
                if body[key] != assertion[key]:
                    return False, f"Invalid value for key {key}: assert {body[key]}=={assertion[key]}"
        return True, None