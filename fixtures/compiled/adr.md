Decision: the order worker reads from Amazon SQS.

Consequence: publishers do not wait for the worker. SQS retries a failed message three times. Then the message goes to the dead-letter queue.
