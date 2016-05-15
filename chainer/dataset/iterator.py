class Iterator(object):

    """Base class of all dataset iterators.

    Iterator iterates over the dataset, yielding a minibatch at each
    iteration. Minibatch is a list of examples. Each implementation should
    implement an iterator protocol (e.g., the :meth:`next` method).

    Note that, even if the iterator supports setting the batch size, it does
    not guarantee that each batch always contains the same number of examples.
    For example, if you let the iterator to stop at the end of the sweep, the
    last batch may contain a fewer number of examples.

    The interface between the iterator and the underlying dataset is not fixed,
    and up to the implementation.

    Each implementation should provide the following attributes (or possibly
    read-only properties).

    - ``batch_size``: the number of examples within each batch.
    - ``current_position``: the current position of the iterator within the
       epoch.
    - ``epoch``: the number of completed sweeps over the dataset.
    - ``is_new_epoch``: True if the epoch count was incremented at the last
      update.

    Each implementation should also support serialization to resume/suspend the
    iteration.

    """
    def __iter__(self):
        """Returns self."""
        return self

    def next(self):
        """Returns the next batch.

        This is a part of the iterator protocol of Python. It may raises the
        :class:`StopIteration` exception when it stops the iteration.

        """
        raise NotImplementedError

    def finalize(self):
        """Finalizes the iterator and possibly releases the resources.

        This method does nothing by default. Implementation may override it to
        better handle the internal resources.

        """
        pass

    def serialize(self, serializer):
        """Serializes the internal state of the iterator.

        This is a method to support serializer protocol of Chainer.

        .. note::
           It should only serializes the internal state that changes over the
           iteration. It should not serializes what is set manually by
           users such as the batch size.

        """
        pass
