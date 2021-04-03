


zip -r9 ../lambdas.zip . -x \*.git\* -x \*.pyc\* -x \*__pycache__\*


aws s3 cp ../lambdas.zip s3://bucket/_lambdas/lambdas3.zip



