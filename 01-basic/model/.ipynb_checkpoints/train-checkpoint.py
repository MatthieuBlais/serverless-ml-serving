from __future__ import print_function

import argparse
import logging
import os
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np
import csv
import pickle

logging.basicConfig(level=logging.DEBUG)

class SmallLSTM(tf.keras.Model):
    
    def __init__(self, vocab_size):
        super(SmallLSTM, self).__init__()
        self.embedding = tf.keras.layers.Embedding(vocab_size, 32, input_length=200)
        self.lstm = tf.keras.layers.LSTM(50)
        self.dropout = tf.keras.layers.Dropout(0.2)
        self.d1 = tf.keras.layers.Dense(1, activation='sigmoid')
    
    def call(self, x):
        x = self.embedding(x)
        x = self.lstm(x)
        x = self.dropout(x)
        return self.d1(x)
    
def get_dataset(path, train=True):
    sentences = []
    labels = []
    if train:
        filename = path + "/train.csv"
    else:
        filename = path + "/test.csv"
    with open(filename, "r") as f:
        reader = csv.reader(f, delimiter=",")
        next(reader)
        for tweet in reader:
            sentences.append(tweet[0].strip())
            labels.append(float(tweet[1]))
    return sentences, labels

def preprocess(tokenizer, sentences, labels, max_length=200):
    encoded_docs = tokenizer.texts_to_sequences(sentences)
    return np.array(pad_sequences(encoded_docs, maxlen=max_length)), np.array(labels)

def train(args):
    # create data loader from the train / test channels
    x_train, y_train = get_dataset(args.train, train=True)
    x_test, y_test = get_dataset(args.test, train=False)

    # Prepare tokenizer
    tokenizer = Tokenizer(num_words=args.num_words)
    tokenizer.fit_on_texts(x_train)
    vocab_size = len(tokenizer.word_index) + 1
    
    # Preprocess
    x_train, y_train = preprocess(tokenizer, x_train, y_train)
    x_test, y_test = preprocess(tokenizer, x_test, y_test)

    model = SmallLSTM(vocab_size)
    optimizer = tf.keras.optimizers.Adam(learning_rate=args.learning_rate)
    model.compile(loss='binary_crossentropy', optimizer=optimizer, metrics=['accuracy'])
    model.fit(x_train, y_train, epochs=args.epochs, validation_data=(x_test, y_test))

    # Save the model
    # A version number is needed for the serving container
    # to load the model
    version = '00000000'
    ckpt_dir = os.path.join(args.model_dir, version)
    if not os.path.exists(ckpt_dir):
        os.makedirs(ckpt_dir)
    model.save(ckpt_dir)
    tokenizer_dir = os.path.join(args.model_dir, version)
    with open(tokenizer_dir+'/tokenizer.pickle', 'wb') as handle:
        pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return
    


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--epochs', type=int, default=1)
    parser.add_argument('--learning-rate', type=float, default=1e-4)
    parser.add_argument('--num-words', type=int, default=5000)
    
    # Environment variables given by the training image
    parser.add_argument('--model-dir', type=str, default=os.environ['SM_MODEL_DIR'])
    parser.add_argument('--train', type=str, default=os.environ['SM_CHANNEL_TRAINING'])
    parser.add_argument('--test', type=str, default=os.environ['SM_CHANNEL_TESTING'])
#     parser.add_argument('--model-dir', type=str)
#     parser.add_argument('--train', type=str)
#     parser.add_argument('--test', type=str)

    return parser.parse_args()



if __name__ == '__main__':
    args = parse_args()
    train(args)
