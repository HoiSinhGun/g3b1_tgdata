# Standard import
import importlib
import unittest

from g3b1_data.entities import ENT_TY_tst_tplate
from trans.data.model import TstTplate_, Lc

from g3b1_serv.utilities import *


class SettingsTestCase(unittest.TestCase):
    def test_setng_ref_li(self):
        def get_and_print_members(cls_str: str):
            print(f'\nfor class: {cls_str}')
            cls = getattr(importlib.import_module("trans.data.model"), cls_str)
            getmembers = inspect.getmembers(cls)
            for tup in [i for i in getmembers if i[0][:2] != '__' and not inspect.isfunction(i[1])]:
                print(tup[0].ljust(15) + f' = {tup[1]}')

        def print_members_of_ent_ty(ent_ty: Entity):
            ent_type = getattr(
                importlib.import_module(f'{ent_ty.g3_m_str}.data.model'), f'{ent_ty.type}_'
            )
            print(', '.join([i[0] for i in extract_ele_members(ent_type)]))

        def print_members_of_tst_tplate_(tst_tplate_: TstTplate_):
            print(', '.join([i[0] for i in extract_ele_members(tst_tplate_)]))

        # sel_cu_setng_ref_li
        # Load "module.submodule.my_class"
        my_class = getattr(importlib.import_module("trans.data.model"), "Txtlc")
        # Instantiate the class (pass arguments to the constructor, if needed)
        print('\n'.join([i for i in dir(my_class) if i[:2] != '__']) + '\n\n')

        print_members_of_ent_ty(ENT_TY_tst_tplate)
        row: dict = {'bkey': 'test', 'tst_type': 'blanks', 'id': 666, 'descr': '', 'user_id': None,
                     'lc': Lc.VI, 'lc2': Lc.EN}
        print_members_of_tst_tplate_(TstTplate_.from_row(row))
        get_and_print_members('TstTplateIt')
        get_and_print_members('TstTplate')
        get_and_print_members('TstTplate_')

        # print('\n'.join(
        #     [type(instance, name).__name__ for name in dir(instance) if name[:2] != '__' and name[-2:] != '__']
        # ) + '\n\n')
        meta_data = getattr(importlib.import_module("trans.data"), "MetaData_TRANS")
        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
