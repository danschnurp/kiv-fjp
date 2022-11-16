#  date: 13. 11. 2022
#  author: Daniel Schnurpfeil
#

from unittest import TestCase

from src.main import main


class Test(TestCase):

    def test_operation(self):
        code = main("../sample_input/operation.swift")
        self.assertEqual(
            """0 INT 0 4
1 LIT 0 222
2 LIT 0 333
3 OPR 0 2
4 STO 0 3
""", code, "operation")

    def test_declaration(self):
        code = main("../sample_input/declaration.swift")
        self.assertEqual("""0 INT 0 4
1 LIT 0 222
2 LIT 0 333
3 OPR 0 2
4 STO 0 3
5 INT 0 4
6 LOD 0 3
7 LIT 0 10
8 OPR 0 2
9 STO 0 4
"""
                         , code, "operation")

    def test_operators(self):
        code = main("../sample_input/operators.swift")
        self.assertEqual("""0 INT 0 4
1 LIT 0 333
2 STO 0 3
3 LIT 0 10
4 LOD 0 3
5 OPR 0 4
6 STO 0 3
""", code, "operators")

    def test_if(self):
        code = main("../sample_input/if.swift")
        self.assertEqual("", code, "if")

    def test_if_else(self):
        code = main("../sample_input/if_else.swift")
        self.assertEqual("", code, "if_else")

    def test_for(self):
        code = main("../sample_input/for.swift")
        self.assertEqual(" ", code, "for")

    def test_for_in_func(self):
        code = main("../sample_input/for_in_func.swift")
        self.assertEqual(" ", code, "for_in_func")

    def test_func(self):
        code = main("../sample_input/func.swift")
        self.assertEqual(" ", code, "func")

    def test_func_simple(self):
        code = main("../sample_input/func_simple.swift")
        self.assertEqual("", code, "func_simple")
