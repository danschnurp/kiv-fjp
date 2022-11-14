#  date: 8. 11. 2022
#  author: Daniel Schnurpfeil
#

from ete3 import Tree

from src.pl0_code_generator.pl0_const import Inst as t, Op as o, SymbolRecord, Pl0Const
from src.pl0_code_generator.pl0_utils import inst, op


# > The class Pl0 is a class that represents a PL/0 program
class Pl0(Pl0Const):

    def __init__(self, abstract_syntax_tree: Tree) -> None:
        """
        The function takes in an abstract syntax tree and initializes the code, ast, and stck attributes.

        :param abstract_syntax_tree: This is the abstract syntax tree that was generated by the parser
        :type abstract_syntax_tree: Tree
        """
        super().__init__()
        self.code = []
        self.ast = abstract_syntax_tree
        self.symbol_table = {}
        self.generate_table_of_symbols(symbols=self.ast.get_leaves())
        self.generate_code(sub_tree=self.clear_tree(self.ast.iter_prepostorder()))

    def generate_instruction(self, inst_name, param1, param2):
        """
        It appends a list of three elements to the list called code

        :param inst_name: The name of the instruction
        :param param1: the first parameter of the instruction
        :param param2: the value of the second parameter
        """
        self.code.append([inst_name, param1, param2])

    def print_code(self):
        """
        It prints the code of the program
        """
        for index, c in enumerate(self.code):
            print(index, "", c[0], c[1], c[2])

    def print_symbol_table(self):
        """
        It prints the symbol table
        """
        for i in self.symbol_table.values():
            if i.type == "func":
                print(i.__str__())
                for j in i.params:
                    print(i.params[j].__str__())
            else:
                print(i.__str__())

    def return_code(self) -> str:
        """
        This function returns a string of the code in the format of "index opcode operand1 operand2"
        :return: The return_code method returns a string of the code.
        """
        code_string = ""
        for index, c in enumerate(self.code):
            code_string += (str(index) + " " + str(c[0]) + " " + str(c[1]) + " " + str(c[2]) + "\n")
        return code_string

    def generate_table_of_symbols(self, level=0, symbols=None):
        """
        It generates a table of symbols
        """
        symbols = symbols
        level = level
        index = 0
        address = 3
        while index < len(symbols):
            ancestor = symbols[index].get_ancestors()[0]
            if ancestor.name == "function_signature":
                if symbols[index].name in self.symbol_table.keys():
                    raise Exception("Duplicate symbol:", symbols[index].name, "in", self.symbol_table.keys())
                params = {}
                for index, i in enumerate(symbols[index].get_sisters()[0].children):
                    id_and_type = i.get_leaf_names()
                    if id_and_type[0] in params.keys():
                        raise Exception("Duplicate symbol:", id_and_type[0], "in", params.keys())
                    params[id_and_type[0]] = (SymbolRecord(id_and_type[0], id_and_type[1], param=True, level=level,
                                                           address=address))
                    address += 1
                self.symbol_table[symbols[index].name] = (
                    SymbolRecord(symbols[index].name, "func", params=params, level=level,
                                 address=address,
                                 return_type=symbols[index].get_sisters()[1].get_leaf_names()[0]))
                address += 1
                func_body = symbols[index].get_sisters()[2].get_leaves()
                # shifting index to skip duplicates
                index += len(func_body)
                # recursive call
                self.generate_table_of_symbols(level=level + 1, symbols=func_body)
            if ancestor.name == "var_declaration_expression":
                if symbols[index].name in self.symbol_table.keys():
                    raise Exception("Duplicate symbol:", symbols[index].name, "in", self.symbol_table.keys())
                self.symbol_table[symbols[index].name] = (SymbolRecord(symbols[index].name,
                                                                       symbol_type=
                                                                       symbols[index].get_sisters()[0].children[0].name,
                                                                       level=level,
                                                                       address=address))
                address += 1
                if ancestor.get_sisters()[0].name == "let":
                    self.symbol_table[symbols[index].name].const = True
            index += 1

    def gen_const(self, const):
        """
        It generates a constant

        :param const: The constant to be generated
        """
        if type(const) == int:
            self.generate_instruction(inst(t.lit), 0, const)

    def gen_opr(self, const1, operator: o, const2):
        """
        It generates instructions for the operation of two constants

        :param const1: The first constant to be used in the operation
        :param operator: o = enum('+', '-', '*', '/', '<', '>', '=', '<=', '>=', '<>', 'and', 'or', 'not', 'neg')
        :type operator: o
        :param const2: The second constant to be used in the operation
        """
        if const1:
            self.gen_const(const1)
        if const2:
            self.gen_const(const2)
        self.generate_instruction(inst(t.opr), 0, str(operator))

    def gen_opr_add(self, const1=None, const2=None):
        self.gen_opr(const1, op(o.add), const2)

    def gen_opr_sub(self, const1=None, const2=None):
        self.gen_opr(const1, op(o.sub), const2)

    def gen_opr_mul(self, const1=None, const2=None):
        self.gen_opr(const1, op(o.mul), const2)

    def gen_opr_div(self, const1=None, const2=None):
        self.gen_opr(const1, op(o.div), const2)

    def gen_term(self, const1=None, const2=None):
        self.gen_const(const1)

    def gen(self, something):
        # dummy method
        pass

    def clear_tree(self, tree_iter_generator):
        sub_tree = []
        for i in tree_iter_generator:
            if not i[0]:
                sub_tree.append(i[1])
        return sub_tree

    def generate_code(self, sub_tree=None):
        sub_tree = list(sub_tree)
        index = 0
        while index < len(sub_tree):
            if sub_tree[index].name in self.expressions:
                leaves = sub_tree[index].get_leaf_names()
                if leaves[0] in self.symbol_table.keys() and leaves[1] in self.symbol_table.keys():
                    self.expressions[sub_tree[index].name]()
                    index += 2
                elif leaves[0] in self.symbol_table.keys():
                    self.gen_load_symbol(self.symbol_table[leaves[0]])
                    self.expressions[sub_tree[index].name](leaves[1])
                    index += 1
                elif leaves[1] in self.symbol_table.keys():
                    self.gen_load_symbol(self.symbol_table[leaves[1]])
                    self.expressions[sub_tree[index].name](leaves[0])
                    index += 1
                else:
                    self.expressions[sub_tree[index].name](leaves[0], leaves[1])
                    index += 2
            if sub_tree[index].name == "var_declaration_expression":
                self.generate_instruction(inst(t.int), 0, 4)
                sub_sub_tree = self.clear_tree(sub_tree[index].children[2].iter_prepostorder())
                # shifting index to skip duplicates
                # recursive call
                self.generate_code(sub_tree=sub_sub_tree)
                self.store_var(self.symbol_table[sub_tree[index].children[0].name])
                index += len(sub_sub_tree)
            index += 1

    def store_var(self, var: SymbolRecord):
        self.generate_instruction(inst(t.sto), var.level, var.address)

    def gen_load_symbol(self, symbol: SymbolRecord):
        self.generate_instruction(inst(t.lod), symbol.level, symbol.address)

    def gen_if_else(self, cond1, operator: o, cond2, statement_true, statement_false):
        self.gen_opr(cond1, operator, cond2)
        self.generate_instruction(inst(t.jmc), 0, "X")
        self.gen(statement_true)
        self.generate_instruction(inst(t.jmp), 0, "Y")
        self.gen(statement_false)
