import boto3
import json
import math

pricing = boto3.client("pricing", region_name=os.environ.get("PRICING_ENDPOINT", "ap-south-1"))

class SagemakerProducts():

    SERVICE_CODE = "AmazonSageMaker"

    @classmethod
    def fetch(cls, location, component="Hosting", compute_type=None):
        """Fetch price for all SageMaker instance types"""
        loop = True
        next_token = None
        results = []
        while loop:
            params = {
                "ServiceCode": cls.SERVICE_CODE,
                "Filters": cls.get_filter(location, component=component, compute_type=compute_type)
            }
            if next_token:
                params["NextToken"] = next_token
            response = pricing.get_products(**params)
            results += [{
                "instanceName": x['product']['attributes']["instanceName"],
                "computeType": x['product']['attributes']['computeType'],
                "vCpu": int(x['product']['attributes'].get('vCpu', 0)),
                "memory": float(x['product']['attributes'].get('memory', '0').replace(" GiB", "")),
                "gpu": int(x['product']['attributes'].get('gpu', '0').replace('N/A', '0')),
                "gpuMemory": int(x['product']['attributes'].get('gpuMemory', '0').replace('N/A', '0')),
                "onDemandUsdPrice": cls.extract_price(x['terms']['OnDemand']),
            } for x in cls.parse_price_list(response['PriceList'])]
            if "NextToken" in response:
                next_token = response["NextToken"]
            else:
                loop = False
        return results


    @classmethod
    def parse_price_list(cls, lst):
        """Convert string into JSON"""
        return [json.loads(x) for x in lst]

    @classmethod
    def extract_price(cls, pricing):
        """Extract OnDemand Pricing"""
        pricing_sku = list(pricing.keys())[0]
        pricing_dimension_key = list(pricing[pricing_sku]["priceDimensions"].keys())[0]
        return float(pricing[pricing_sku]["priceDimensions"][pricing_dimension_key]["pricePerUnit"]["USD"])

    @classmethod
    def get_filter(cls, location, component='Hosting', compute_type=None):
        """Filter AWS products based on product family, location and latest generation"""
        filters = [
            {
                'Type': 'TERM_MATCH',
                'Field': 'location',
                'Value': location
            }, {
                'Type': 'TERM_MATCH',
                'Field': 'productFamily',
                'Value': 'ML Instance'
            }, {
                'Type': 'TERM_MATCH',
                'Field': 'currentGeneration',
                'Value': 'Yes'
            }, {
                'Type': 'TERM_MATCH',
                'Field': 'component',
                'Value': component
            }
        ]
        if compute_type:
            filters.append({
                'Type': 'TERM_MATCH',
                'Field': 'computeType',
                'Value': compute_type
            })
        return filters


class InstanceFilter():

    @classmethod
    def apply(cls, products, min_vcpu=0, max_vcpu=float("inf"), min_memory=0, max_memory=float("inf"), min_gpu=0, max_gpu=float("inf"), min_usd=0, max_usd=float('inf'), instance_types=[], max_instance_types=5):
        """Filter products based on specs"""
        results = [x for x in products if (
            min_vcpu <= x["vCpu"] <= max_vcpu
            and min_memory <= x["memory"] <= max_memory
            and min_gpu <= x["gpu"] <= max_gpu
            and min_usd <= x["onDemandUsdPrice"] <= max_usd
        )]
        if len(instance_types) > 0:
            results = [x for x in results if x['instanceName'] in instance_types]
        results = sorted(results, key=lambda x: x['onDemandUsdPrice'])
        if len(results)>max_instance_types:
            results = cls.limit_instance_types(results, max_instance_types)
        return results


    @classmethod
    def limit_instance_types(cls, instances, max_instance_types):
        """Reduce size of instance types based on distinct vCPU/memory"""
        mem = {}
        for instance in instances:
            if (instance['vCpu'], math.ceil(instance['memory'])) not in mem:
                mem[(instance['vCpu'], math.ceil(instance['memory']))] = instance
        out = [val for val in mem.values()]
        if len(out)>max_instance_types:
            out = sorted(out, key=lambda x: x['onDemandUsdPrice'])
            return out[:max_instance_types]
        return out