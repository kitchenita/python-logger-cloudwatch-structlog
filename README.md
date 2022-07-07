# Logger Cloudwatch Structlog  
  
Logger Cloudwatch Structlog is a Python package that contain that allows logging in an [AWS CloudWatch Log](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/WhatIsCloudWatchLogs.html) compatible way using a JSON format in *serverless services in AWS* (e.g., AWS Lambda). It is easily readable by humans and machines. This library is a wrapper for structlog, you can replicate all the functionalities just using **[structlog](https://www.structlog.org/en/stable/index.html)**. We decided to make this library to make easier our developments.
  
## Installation and updating  
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install *Logger Cloudwatch Structlog* like below.   
  
```bash  
pip install logger_cloudwatch_structlog
```  
  
## Usage  
This library has two structlog processors and functions that configure and returns a logger ready to use in your application. Also, we provided a one-fits-all solution that you can use without taking into account any change.  
  
### Processors  
#### PasswordCensor  
Processor that censor words in ``event_dict``. If you log information has words that are needed to be censured, like passwords, etc., this processor replaces them with ``"*CENSORED*"``. You have to provide a list of string of the key to be censured as argument ``wordlist``.  
  
```python  
from logger_cloudwatch_structlog import PasswordCensor  
import structlog  
  
processors = [  
    ...    
    PasswordCensor(wordlist=["password", "user"])    
    ...]  
  
structlog.configure(  
        processors=processors,        
        ...)
          
logger = structlog.get_logger()  
  
logger.info("msg", peer='127.0.0.1', password="password", user="alice")  
  
```  
This would result among other the following lines to be printed:  
  
```bash  
event='msg' peer='127.0.0.1' user='*CENSORED*' password='*CENSORED*'  
```  
  
#### AWSCloudWatchLogs  
Render a log line compatible with AWS CloudWatch Logs.  This is a copy and modification of `structlog.processors.JSONRenderer`. Render the ``event_dict`` using ``serializer(event_dict, **json_kw)``.  This class is from [serverless-zoom-recordings](https://github.com/openlibraryenvironment/serverless-zoom-recordings).  
  
*Arguments:*  
- callouts: List of strings, they are printed in clear-text on the front of the log line. Only the first two items of this list are called out. Defaults to `None`.  
- serializer: A `json.dumps`-compatible callable that will be used to format the string. Defaults to `json.dumps`.  
- \*\*dumps_kw: Arbitrary keyword arguments. Are passed unmodified to *serializer*.  
  
```python  
from logger_cloudwatch_structlog import AWSCloudWatchLogs  
import structlog  
import json  
  
processors = [  
    ...    
    AWSCloudWatchLogs(callouts=["status", "event"], serializer=json.dumps, sort_keys=False)]  
  
structlog.configure(  
        processors=processors,        
        ...)  
logger = structlog.get_logger()  
  
logger.info("msg", status="wut", peer='127.0.0.1', password="password", user="alice")  
  
```  
This would result among other the following lines to be printed:  
  
```bash  
[INFO] "wut" "msg" {"event": "msg", "status": "wut", "peer": "'127.0.0.1'", "password": "password", "user": "alice"}  
```  
  
### Functions  
* setup_logging → Configure logging for the application.  
* get_logger → Convenience function that returns a structlog logger.  
* setup_and_get_logger →  Configure logging for the application and return the logger. This function is a one-fits-all solution with some possibilities to change the setup.  
  
#### setup_logging()  
This function configure the logging for the application. It has multiple arguments that allow you to have a flexible configuration.  
  
*Arguments*:  
- wordlist_to_censor: List with words to be censored in the event_dict, if they are present. Defaults to `None`.
- callouts: List of strings, they are printed in clear-text on the front of the log line. Only the first two items of this list are called out. Defaults to `None`.  
- serializer: A `json.dumps`-compatible callable that will be used to format the string. Defaults to `json.dumps`.  
- level: Sets the threshold for this logger to level. Logging messages which are less severe than level will be ignored. Defaults to `logging.INFO`.  
- noisy_log_sources: Tuple of sources that output a lot of unnecessary messages. Defaults to `("boto", "boto3", "botocore")`.  
- \*\*serializer_kw: Arbitrary keyword arguments. Are passed unmodified to *serializer*.  
  
#### get_logger()  
Convenience function that returns a structlog logger.  
  
*Arguments*:  
- \*args: Positional arguments that are passed unmodified to the logger factory. Therefore, it depends on the factory what they mean.  
- \*\*initial_values: Values that are used to pre-populate the context.  
  
#### setup_and_get_logger()  
Configure logging for the application and return the logger. This function is a one-fits-all solution with some possibilities to change the setup. But you cannot add keyword arguments for the logger factory, or even values that are used to pre-populate the context. If you need a more flexible solution, you can call setup_logging() and get_logger() separated.  
  
Example,  
```python  
from logger_cloudwatch_structlog import setup_and_get_logger, AWSCloudWatchLogs  
import structlog  
import logging  
  
processors = [structlog.stdlib.add_log_level,  
              structlog.processors.TimeStamper(fmt="iso"),              
              structlog.processors.UnicodeDecoder(),              
              AWSCloudWatchLogs(callouts=["event", "context"])]  
logger = setup_and_get_logger(level=logging.INFO, processors=processors)  
```  
  
### One-fits-all solution  
If you want to use this library without any change, we provide a one-fit-solution. If you call `setup_and_get_logger()` without argument, you have a ready to use logger that works with AWS CloudWatch Log.  
  
```python  
from logger_cloudwatch_structlog import setup_and_get_logger  
  
logger = setup_and_get_logger()  
```  
  
The one-fits-all solution has the next configuration:  
```python  
wordlist_to_censor=None  
callouts=["status_code", "event"]  
serializer=json.dumps  
level=logging.INFO  
noisy_log_sources=("boto", "boto3", "botocore")  
processors = (  
    structlog.stdlib.filter_by_level,    
    structlog.stdlib.add_log_level,    
    structlog.stdlib.PositionalArgumentsFormatter(),    
    structlog.processors.TimeStamper(fmt="iso"),    
    structlog.processors.StackInfoRenderer(),  
    structlog.processors.format_exc_info,    
    structlog.processors.UnicodeDecoder(),    
    PasswordCensor(wordlist=wordlist_to_censor),    
    structlog.threadlocal.merge_threadlocal,    
    AWSCloudWatchLogs(callouts=["status_code", "event"], 
    serializer=json.dumps, sort_keys=False))  
```  
  
If you want words to be censored, just add the list in the function  
```python  
from logger_cloudwatch_structlog import setup_and_get_logger  
  
logger = setup_and_get_logger(wordlist_to_censor=["password"])  
```

## License  
[Apache 2.0](https://choosealicense.com/licenses/apache-2.0/)
