import unittest

from elements import ELE_TY_sel_idx_rng
from g3b1_cfg import tg_cfg


class MyTestCase(unittest.TestCase):
    def test_something(self):
        cls = tg_cfg.sel_ele_ty_cls(ELE_TY_sel_idx_rng)
        self.assertEqual(ELE_TY_sel_idx_rng, cls.ele_ty())


if __name__ == '__main__':
    unittest.main()
