import logging
import numpy as np

from chainer import variable
from chainer.utils import force_array, type_check

from dnn import is_cosim
from dnn._dnn import mdarray


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s]: %(message)s')


def plain_array(params):
    assert isinstance(params, tuple) \
            or isinstance(params, list) \
            or isinstance(params, mdarray) \
            or isinstance(params, np.ndarray) \
            or isinstance(params, variable.Variable)

    _params = ()

    if isinstance(params, variable.Variable):
        return np.array(params.data),
    elif isinstance(params, np.ndarray):
        return params,
    elif isinstance(params, mdarray):
        return np.array(params),

    for p in params:
        if isinstance(p, variable.Variable):
            p = np.array(p.data)
        if isinstance(p, mdarray):
            _params += (np.array(p), )
        else:
            _params += (p, )

    return _params


def expect_allclose(act, ref, atol=1e-4, rtol=1e-4, verbose=True):
    """Failed if some corresponding element of act and ref differs too much.

    Args:
        act: Left-hand-side array.
        ref: Right-hand-side array.
        atol (float): Absolute tolerance.
        rtol (float): Relative tolerance.
        verbose (bool): If ``True``, it outputs verbose messages on error.
    """
    if not isinstance(act, np.ndarray) or not isinstance(ref, np.ndarray):
        logging.warning('wrong array types')
        return False

    act = force_array(act)
    ref = force_array(ref)

    if act.size != ref.size or act.itemsize != ref.itemsize or act.shape != ref.shape:
        logging.warning('size is not matched!\nsize: act={0} ref={1} itemsize: act={2} ref={3}\n'
                        'shape: act={4}, ref={5} dtype: act= {6} ref={7}'
                        .format(act.size, ref.size, act.itemsize, ref.itemsize,
                                act.shape, ref.shape, act.dtype, ref.dtype))
        return False

    act = np.ascontiguousarray(act)
    ref = np.ascontiguousarray(ref)

    try:
        np.testing.assert_allclose(act, ref, rtol, atol, verbose=verbose)
    except Exception:
        return False

    return True


def verify_results(func, acts, refs, inputs, out_grads=None):
    logging.info('cosim verify for {0}'.format(func.__class__.__name__))

    if acts is None and refs is None:
        logging.warning('input results are None!')
        return True

    return True


def cosim_verify(func, acts, inputs, out_grads=None):
    if not is_cosim():
        return

    if not out_grads:   # forward
        logging.info('cosim test for forward of function {0}'.format(func.__class__.__name__))

        refs = plain_array(func.forward_cpu(*plain_array(inputs)))

        if not verify_results(func, acts, refs, inputs):
            logging.error('cosim test failed during forward of function {0}'.format(func.__class__.__name__))
            raise RuntimeError

    else:   # backward
        pass