from chainer import cuda
from chainer import function
from chainer.utils import type_check
import numpy


class ClippedReLU(function.Function):

    """Clipped Rectifier Unit function.

    Clipped ReLU is written as :math:`ClippedReLU(x, z) = \min(\max(0, x) ,z)`,
    where :math:`z(>0)` is a parameter to cap return value of ReLU.

    """

    def __init__(self, z):
        if not isinstance(z, float):
            raise TypeError('z must be float value')
        # z must be positive.
        assert(z > 0)
        self.cap = z

    def check_type_forward(self, in_types):
        type_check.expect(in_types.size() == 1)
        x_type, = in_types
        type_check.expect(x_type.dtype == numpy.float32)

    def check_type_backward(self, in_types, out_types):
        type_check.expect(
            in_types.size() == 1,
            out_types.size() == 1
        )
        x_type, = in_types
        y_type, = out_types
        type_check.expect(
            y_type.dtype == numpy.float32,
            y_type.ndim == x_type.ndim)

    def forward_cpu(self, x):
        return numpy.array(numpy.minimum(numpy.maximum(0, x[0]), self.cap),
                           dtype=numpy.float32),

    def backward_cpu(self, x, gy):
        return numpy.array(gy[0] * (0 < x[0]) * (x[0] < self.cap)),

    def forward_gpu(self, x):
        return cuda.gpuarray.minimum(cuda.gpuarray.maximum(0, x[0]), self.cap),

    def backward_gpu(self, x, gy):
        gx = cuda.empty_like(x[0])
        cuda.elementwise(
            'float* gx, const float* x, const float* gy, const float z',
            'gx[i] = ((x[i] > 0) and (x[i] < z))? gy[i] : 0',
            'clipped_relu_bwd')(gx, x[0], gy[0], self.cap)
        return gx,


def clipped_relu(x, z=20.0):
    """Clipped Rectifier Unit function.

    This function is expressed as :math:`CReLU(x, z) = \min(\max(0, x), z),
    where :math:`z(>0)` is a clipping value.

    Args:
        x (~chainer.Variable): Input variable, which is n(>0)-dimensional array
        z (float): clipping value. (default = 20.0)

    Returns:
        ~chainer.Variable: Output variable.

    """
    return ClippedReLU(z)(x)
