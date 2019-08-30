#!/usr/bin/env python3

from array import array
from PIL import Image

TEST_PARAMS = [
    #(0x00, 0xFF, 256, 1.0, (256, 10)),  # High-effort sanity check
    (0x00, 0xFF, 30, 0.5, (500, 100)),
    (0x00, 0xFF, 30, 0.8, (500, 100)),
    (0x00, 0xFF, 30, 1.0, (500, 100)),
    (0x00, 0xFF, 30, 1.3, (500, 100)),
    (0x00, 0xFF, 30, 1.8, (500, 100)),
    (0x00, 0xFF, 30, 2.0, (500, 100)),
    (0x00, 0xFF, 30, 2.2, (500, 100)),
    (0x00, 0xFF, 30, 2.5, (500, 100)),
    (0x00, 0xFF, 30, 4.0, (500, 100)),
    (0x00, 0xFF, 256, 1.0, (500, 100)),
]


def v_to_int(v):
    return max(0, min(int(v * 255 + 0.5), 255))


def make_gamma_interp(src_l, dst_l, quants, gamma, size):
    assert quants >= 2
    w, h = size
    invgamma = 1 / gamma
    src_v = src_l / 255
    dst_v = dst_l / 255
    src_g = src_v ** invgamma
    dst_g = dst_v ** invgamma
    all_g = [src_g + (dst_g - src_g) * i / (quants - 1) for i in range(quants)]
    all_v = [g ** gamma for g in all_g]
    all_x = [(v - src_v) / (dst_v - src_v) for v in all_v]
    assert -1e-9 < all_v[0] - src_v < +1e-9, all_v
    assert -1e-9 < all_v[-1] - dst_v < +1e-9, all_v

    # Lots of sanity checking
    # Otherwise, the drawing code crashes horribly and without any good reason why.
    assert -1e-9 < all_x[0] - 0 < +1e-9, all_x
    assert -1e-9 < all_x[-1] - 1 < +1e-9, all_x
    assert 0 < all_x[1]
    assert all_x[-2] < 1
    assert all(all_x[i] < all_x[i + 1] for i in range(quants - 1))
    all_v[0] = src_v
    all_v[-1] = dst_v
    all_x[0] = 0.0
    all_x[-1] = 1.0
    all_x.append(3.0)  # Must have large distance:
    # During the last quantum, the drawing code needs to check whether it
    # needs to switch to the next quantum.  Sure, I could just write that as a
    # separate loop, but I prefer dummy data over code duplication.

    cur_i = 0
    cur_l = v_to_int(all_v[cur_i])
    cur_x = all_x[cur_i]
    next_x = all_x[cur_i + 1]
    rowdata = []
    for here_px in range(w):
        here_x = here_px / (w - 1)
        if next_x - here_x < here_x - cur_x:
            cur_i += 1
            cur_l = v_to_int(all_v[cur_i])
            cur_x = all_x[cur_i]
            next_x = all_x[cur_i + 1]  # ← Potentially reads dummy value
        rowdata.append(cur_l)

    # High-effort sanity check:
    if (src_l, dst_l, quants, gamma, size[0]) == (0, 255, 256, 1.0, 256):
        print('\tHigh-effort sanity check')
        assert rowdata == list(range(256))
        print('\tPassed')

    img = Image.new('L', size)
    img.putdata(rowdata * h)
    return img


def save_gamma_interp(src_l, dst_l, quants, gamma, size):
    filename = 'results/gamma_interp_from0x{:02x}_to0x{:02x}_q{}_g{:.2}_{}x{}.png'.format(
        src_l, dst_l, quants, gamma, size[0], size[1],
    )
    print('Making {}'.format(filename))
    img = make_gamma_interp(src_l, dst_l, quants, gamma, size)
    img.save(filename)


if __name__ == '__main__':
    for params in TEST_PARAMS:
        save_gamma_interp(*params)
    print('All done.')
