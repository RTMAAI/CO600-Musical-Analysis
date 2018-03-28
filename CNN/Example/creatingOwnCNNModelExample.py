import os
import numpy as np
import tensorflow as tf
from random import shuffle
import pickle

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

''' Uses this model uses Tensorflow's MNIST Tutorial as a foundation '''
''' This is the CNN model used to create the trained model for the genre predictor '''

tf.logging.set_verbosity(tf.logging.INFO)

def genre_cnn_model_fn(features, labels, mode):
    '''adasdas'''
    input_layer = tf.reshape(features["x"], [-1, 128, 128, 1])

    print(input_layer.get_shape())

    # Convolutional Layer #1 and Pooling Layer #1
    conv1 = tf.layers.conv2d(
        inputs=input_layer,
        filters=64,
        kernel_size=[2, 2],
        padding="same",
        activation=tf.nn.relu)
    pool1 = tf.layers.max_pooling2d(inputs=conv1, pool_size=[2, 2], strides=2)

    # Convolutional Layer #2 and Pooling Layer #2
    conv2 = tf.layers.conv2d(
        inputs=pool1,
        filters=128,
        kernel_size=[2, 2],
        padding="same",
        activation=tf.nn.relu)
    pool2 = tf.layers.max_pooling2d(inputs=conv2, pool_size=[2, 2], strides=2)

    # Convolutional Layer #3 and Pooling Layer #3
    conv3 = tf.layers.conv2d(
        inputs=pool2,
        filters=256,
        kernel_size=[2, 2],
        padding="same",
        activation=tf.nn.relu)
    pool3 = tf.layers.max_pooling2d(inputs=conv3, pool_size=[2, 2], strides=2)

    # Convolutional Layer #3 and Pooling Layer #3
    conv4 = tf.layers.conv2d(
        inputs=pool3,
        filters=512,
        kernel_size=[2, 2],
        padding="same",
        activation=tf.nn.relu)
    pool4 = tf.layers.max_pooling2d(inputs=conv4, pool_size=[2, 2], strides=2)

    # Convolutional Layer #3 and Pooling Layer #3
    conv5 = tf.layers.conv2d(
        inputs=pool4,
        filters=1024,
        kernel_size=[2, 2],
        padding="same",
        activation=tf.nn.relu)
    pool5 = tf.layers.max_pooling2d(inputs=conv5, pool_size=[2, 2], strides=2)

    # Dense Layer
    pool5_flat = tf.contrib.layers.flatten(pool5)
    print(pool5_flat.get_shape())
    dense = tf.layers.dense(inputs=pool5_flat, units=2048, activation=tf.nn.relu)
    dropout = tf.layers.dropout(inputs=dense, rate=0.5, training=mode == tf.estimator.ModeKeys.TRAIN)

    # Logits Layer
    logits = tf.layers.dense(inputs=dropout , units=4)

    # Generate predictions (for PREDICT and EVAL mode)
    predictions = {
        
        "classes": tf.argmax(input=logits, axis=1),
        # Add `softmax_tensor` to the graph. It is used for PREDICT and by the `logging_hook`.
        "probabilities": tf.nn.softmax(logits, name="softmax_tensor")
    }

    if mode == tf.estimator.ModeKeys.PREDICT:
        export_outputs = {'predict_output': tf.estimator.export.PredictOutput({"classes": tf.argmax(input=logits, axis=1), 'probabilities': tf.nn.softmax(logits)})}
        return tf.estimator.EstimatorSpec(mode=mode, predictions= predictions, export_outputs=export_outputs)

    # Calculate Loss (for both TRAIN and EVAL modes)
    onehot_labels = tf.one_hot(indices=tf.cast(labels, tf.int32), depth=4)
    loss = tf.losses.softmax_cross_entropy(onehot_labels=onehot_labels, logits=logits)

    # Configure the Training Op (for TRAIN mode)
    if mode == tf.estimator.ModeKeys.TRAIN:
        optimizer = tf.train.RMSPropOptimizer(learning_rate=0.001)
        train_op = optimizer.minimize(
            loss=loss,
            global_step=tf.train.get_global_step())
        return tf.estimator.EstimatorSpec(mode=mode, loss=loss, train_op=train_op)

    # Add evaluation metrics (for EVAL mode)
    eval_metric_ops = {"accuracy": tf.metrics.accuracy(labels=labels, predictions=predictions["classes"])}
        
    return tf.estimator.EstimatorSpec(mode=mode, loss=loss, eval_metric_ops=eval_metric_ops)


def serving_input_receiver_fn():
    """Build the serving input."""

    inputs = {"x": tf.placeholder(shape=[1, 128,128,1], dtype=tf.float32)}
    return tf.estimator.export.ServingInputReceiver(inputs, inputs)


def main(mode):
    print("Welcome to Spectrogram CNN Model creator.")
    print("Enter T if you want to train a new model.")
    print("Enter E if you want to evaluate a model.")
    print("Enter Q if you want to quit.")

    choice = input('Enter option: ')

    correct_choice = True

    # Create the Estimator
    genre_classifier = tf.estimator.Estimator(
        model_fn=genre_cnn_model_fn, 
        model_dir=os.path.join(os.path.dirname(__file__),
        "Example_New_Model/model"))
    
    while correct_choice:
        if choice == 'T' or choice == 't':
            print ("Loading Dataset...")
            print()

            try:
                with open(os.path.join(os.path.dirname(__file__),"Training_Dataset/spectrogram_traningX"), 'rb') as f:
                    train_data = pickle.load(f)
                train_data = np.asarray(train_data)
                train_data = train_data.astype('float32')
            except:
                print("spectrogram_traningX File within Training_Dataset Folder does not exist. Please run creatingOwnDpectrogram.py ")
                break

            try:
                with open(os.path.join(os.path.dirname(__file__),"Training_Dataset/spectrogram_traningY"), 'rb') as f:
                    train_labels = pickle.load(f)
                train_labels = np.asarray(train_labels)
                train_labels = train_labels.astype('float32')
            except:
                print("spectrogram_traningY File within Training_Dataset Folder does not exist. Please run creatingOwnDpectrogram.py ")
                break

            try:
                with open(os.path.join(os.path.dirname(__file__),"Evaluator_Dataset/spectrogram_evaluX"), 'rb') as f:
                    eval_data = pickle.load(f)
                eval_data = np.asarray(eval_data)
                eval_data = eval_data.astype('float32')
            except:
                print("spectrogram_evaluX File within Evaluator_Dataset Folder does not exist. Please run creatingOwnDpectrogram.py ")
                break

            try:
                with open(os.path.join(os.path.dirname(__file__),"Evaluator_Dataset/spectrogram_evaluY"), 'rb') as f:
                    eval_labels = pickle.load(f)
                eval_labels = np.asarray(eval_labels)
                eval_labels = eval_labels.astype('float32')
            except:
                print("spectrogram_evaluX File within Evaluator_Dataset Folder does not exist. Please run creatingOwnDpectrogram.py ")
                break

            print ("Success")

            correct_choice = False
            # Set up logging for predictions
            # Log the values in the "Softmax" tensor with label "probabilities"
            tensors_to_log = {"probabilities": "softmax_tensor"}
            logging_hook = tf.train.LoggingTensorHook(tensors=tensors_to_log, every_n_iter=50)

            # Train the model
            train_input_fn = tf.estimator.inputs.numpy_input_fn(
                x={"x": train_data},
                y=train_labels,
                batch_size=1,
                num_epochs=None,
                shuffle=True)
            genre_classifier.train(
                input_fn=train_input_fn,
                steps=10000,
                hooks=[logging_hook])

            eval_input_fn = tf.estimator.inputs.numpy_input_fn(
                x={"x": eval_data},
                y=eval_labels,
                num_epochs=1,
                shuffle=False)

            eval_results = genre_classifier.evaluate(input_fn=eval_input_fn)
            print(eval_results)
            full_model_dir = genre_classifier.export_savedmodel(export_dir_base=os.path.join(os.path.dirname(__file__), "New_Model_Exported/model" ), serving_input_receiver_fn=serving_input_receiver_fn)
    

        elif choice == 'E' or choice == 'e':
            correct_choice = False
            print ("Starting evlaution...")

            print ("Loading Evalution Spectrogram Data...")
            with open(os.path.join(os.path.dirname(__file__),"Evaluator_Dataset/spectrogram_evaluX"), 'rb') as f:
                eval_data = pickle.load(f)
            eval_data = np.asarray(eval_data)
            eval_data = eval_data.astype('float32')

            print ("Succuess")

            print ("Loading Evalution Spectrogram Labels...")
            with open(os.path.join(os.path.dirname(__file__),"Evaluator_Dataset/spectrogram_evaluY"), 'rb') as f:
                eval_labels = pickle.load(f)
            eval_labels = np.asarray(eval_labels)
            eval_labels = eval_labels.astype('float32')
            
            print ("Succuess")

            print("Evaluating...")

            # Evaluate the model and print results
            eval_input_fn = tf.estimator.inputs.numpy_input_fn(
                x={"x": eval_data},
                y=eval_labels,
                num_epochs=1,
                shuffle=False)

            try:
                eval_results = genre_classifier.evaluate(input_fn=eval_input_fn)
                print(eval_results)
            except:
                print("Error: You must create a model first")

        elif choice == Q or choice == q:
            print ("Quit...")
            break
        else:
            print("Try again...")
        


if __name__ == "__main__":
  tf.app.run()

