import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='logger_cloudwatch_structlog',
    version='0.1.0',
    author='Kitchenita, Facundo A. Lucianna',
    author_email='facundo@kitchenita.co',
    description='Python library that allows logging in an AWS CloudWatch compatible way using a json format in '
                'serverless services (e.g. AWS Lambda). It is easily readable by humans and machines.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/kitchenita/python-logger-cloudwatch-structlog',
    project_urls={
        "Bug Tracker": "https://github.com/kitchenita/python-logger-cloudwatch-structlog/issues"
    },
    packages=['logger_cloudwatch_structlog'],
    install_requires=['structlog>=22.2'],
)
