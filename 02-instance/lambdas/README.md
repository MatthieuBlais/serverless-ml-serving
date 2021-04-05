


zip -r9 ../lambdas.zip . -x \*.git\* -x \*.pyc\* -x \*__pycache__\*

mkdir ../packages
pip3 install -r requirements.txt --target ../packages
cd ../packages
zip -g -r ../lambdas.zip . -x \*.git\* -x \*.pyc\* -x \*__pycache__\*

cd ..
rm -rf packages

aws s3 cp lambdas.zip s3://ml-serving-perftest/_lambdas/lambdas3.zip
