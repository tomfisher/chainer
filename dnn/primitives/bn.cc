/*
 *COPYRIGHT
 *All modification made by Intel Corporation: © 2017 Intel Corporation.
 *Copyright (c) 2015 Preferred Infrastructure, Inc.
 *Copyright (c) 2015 Preferred Networks, Inc.
 *
 *Permission is hereby granted, free of charge, to any person obtaining a copy
 *of this software and associated documentation files (the "Software"), to deal
 *in the Software without restriction, including without limitation the rights
 *to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 *copies of the Software, and to permit persons to whom the Software is
 *furnished to do so, subject to the following conditions:
 *
 *The above copyright notice and this permission notice shall be included in
 *all copies or substantial portions of the Software.
 *
 *THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 *IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 *FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 *AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 *LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 *OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 *THE SOFTWARE.
 *
 */


#include <mkldnn.hpp>
#include <vector>
#include <memory>
#include "layer.h"
#include "tensor.h"
#include "bn.h"
#include "bn_fwd.h"
#include "bn_bwd.h"
#include "prim_factory.h"
#include "reorder_op.h"

template<typename T>
std::vector<Tensor *> batch_normalization<T>::Forward(
    Tensor *src, Tensor *w, Tensor *mean, Tensor *var, float eps) {

    assert(memory_data_type<T>() == src.cxx_data_type());

    bool scale_shift = w ? true : false;
    bool global_stats = mean ? true : false;
    bool training = mean ? false : true;

    auto bn_fwd = batch_normalization_fwd_factory<T>::get(
            (mkldnn::memory::dims)src->dims(),
            eps, scale_shift, global_stats, training);

    void *src_data = src->data();
    void *src_itnl = nullptr;
    if (src->cxx_format() != bn_fwd->get_src_fmt()) {
        auto reorder = ReorderFactory<T>::get(
            (mkldnn::memory::dims)src->dims(),
            (mkldnn::memory::format)src->cxx_format(),
            (mkldnn::memory::format)bn_fwd->get_src_fmt());
        src_itnl = new avx::byte[src->len()];
        reorder->execute(src_data, src_itnl);
        src_data = src_itnl;
    }

    auto dst = new Tensor(src->ndims(), src->dims(),
                          (mkldnn_memory_format_t)bn_fwd->get_dst_fmt(),
                          src->type());
    mean = training ?
           new Tensor(bn_fwd->get_mean_ndims(), bn_fwd->get_mean_dims(),
                      (mkldnn_memory_format_t)bn_fwd->get_mean_fmt(),
                      src->type()) : mean;
    var = training ?
          new Tensor(bn_fwd->get_var_ndims(), bn_fwd->get_var_dims(),
                     (mkldnn_memory_format_t)bn_fwd->get_var_fmt(),
                     src->type()) : var;

    bn_fwd->execute(src_data, (w ? w->data() : nullptr),
                    dst->data(), (mean ? mean->data() : nullptr),
                    (var ? var->data() : nullptr));

    std::vector<Tensor *> outs;
    outs.push_back(dst);
    if (training) {
        outs.push_back(mean);
        outs.push_back(var);
    }

    if (src_itnl)
        delete static_cast<avx::byte *>(src_itnl);

    return outs;
}

template<typename T>
std::vector<Tensor *> batch_normalization<T>::Backward(
            Tensor *src, Tensor *diff_dst, Tensor *mean,
            Tensor *var, Tensor *w, float eps) {

    assert(memory_data_type<T>() == src.cxx_data_type());

    bool scale_shift = w ? true : false;

    auto bn_bwd = batch_normalization_bwd_factory<T>::get(
            (mkldnn::memory::dims)src->dims(),
            (mkldnn::memory::dims)diff_dst->dims(),
            eps, scale_shift);

    void *src_data = src->data();
    void *src_itnl = nullptr;
    if (src->cxx_format() != bn_bwd->get_src_fmt()) {
        auto reorder = ReorderFactory<T>::get(
            (mkldnn::memory::dims)src->dims(),
            (mkldnn::memory::format)src->cxx_format(),
            (mkldnn::memory::format)bn_bwd->get_src_fmt());
        src_itnl = new avx::byte[src->len()];
        reorder->execute(src_data, src_itnl);
        src_data = src_itnl;
    }

    void *diff_dst_data = diff_dst->data();
    void *diff_dst_itnl = nullptr;
    if (diff_dst->cxx_format() != bn_bwd->get_diff_dst_fmt()) {
        auto reorder = ReorderFactory<T>::get(
            (mkldnn::memory::dims)diff_dst->dims(),
            (mkldnn::memory::format)diff_dst->cxx_format(),
            (mkldnn::memory::format)bn_bwd->get_diff_dst_fmt());
        diff_dst_itnl = new avx::byte[diff_dst->len()];
        reorder->execute(diff_dst_data, diff_dst_itnl);
        diff_dst_data = diff_dst_itnl;
    }

    auto diff_src = new Tensor(src->ndims(), src->dims(),
                    (mkldnn_memory_format_t)bn_bwd->get_diff_src_fmt(),
                    src->type());
    auto diff_w = scale_shift ?
                  new Tensor(w->ndims(), w->dims(),
                  (mkldnn_memory_format_t)bn_bwd->get_diff_w_fmt(),
                  w->type()) : (Tensor *)(nullptr);

    bn_bwd->execute(src_data, diff_dst_data, mean->data(), var->data(),
                    (w ? w->data() : nullptr), diff_src->data(),
                    (diff_w ? diff_w->data() : nullptr));

    std::vector<Tensor *> outs;
    outs.push_back(diff_src);
    if (scale_shift)
        outs.push_back(diff_w);

    if (src_itnl)
        delete static_cast<avx::byte *>(src_itnl);

    if (diff_dst_itnl)
        delete static_cast<avx::byte *>(diff_dst_itnl);

    return outs;
}

template class batch_normalization<float>;