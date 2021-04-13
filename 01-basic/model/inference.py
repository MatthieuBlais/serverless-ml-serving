import pickle
import json
import numpy as np
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

VERSION = "00000000"
TOKENIZER_FILENAME = "tokenizer.pickle"

tokenizer = None
with open(f'/opt/ml/model/{VERSION}/{TOKENIZER_FILENAME}', 'rb') as handle:
    tokenizer = pickle.load(handle)
    
def preprocess(tokenizer, sentences, max_length=200):
    encoded_docs = tokenizer.texts_to_sequences(sentences)
    return np.array(pad_sequences(encoded_docs, maxlen=max_length))
    
def input_handler(data, context):
    """ Pre-process request input before it is sent to TensorFlow Serving REST API
    Args:
        data (obj): the request data, in format of dict or string
        context (Context): an object containing request and configuration details
    Returns:
        (dict): a JSON-serializable dict that contains request body and headers
    """
    sentence = data.read().decode('utf-8')
    return json.dumps({
        'instances': [[int(y) for y in list(x)] for x in list(preprocess(tokenizer, [sentence]))]
    })


def output_handler(data, context):
    """Post-process TensorFlow Serving output before it is returned to the client.
    Args:
        data (obj): the TensorFlow serving response
        context (Context): an object containing request and configuration details
    Returns:
        (bytes, string): data to return to client, response content type
    """
    if data.status_code != 200:
        raise Exception(data.content.decode('utf-8'))
    response_content_type = context.accept_header
    print(data.content)
    prediction = data.content
    return prediction, response_content_type