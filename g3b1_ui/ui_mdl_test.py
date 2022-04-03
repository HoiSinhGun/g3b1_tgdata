import unittest

from constants import env_g3b1_code
from py_meta import read_classes, build_module_str
from g3b1_ui import ui_mdl


class MyTestCase(unittest.TestCase):
    def test_something(self):
        class_li = read_classes(ui_mdl.__file__)
        rel_file_path = ui_mdl.__file__.replace(env_g3b1_code, '')
        print(rel_file_path)
        print(build_module_str(ui_mdl.__file__))
        print('\n'.join([c.name for c in class_li]))
        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
