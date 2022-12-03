#  date: 8. 11. 2022
#  author: Daniel Schnurpfeil
#
from copy import copy

from ete3 import Tree

from src.pl0_code_generator.pl0_const import Inst as Inst, Op as Op, SymbolRecord, Pl0Const, inst, op


# > The class Pl0 is a class that represents a PL/0 program
class Pl0(Pl0Const):

    def __init__(self, abstract_syntax_tree: Tree, symbol_table) -> None:
        """
        The function takes in an abstract syntax tree and initializes the code, ast, and stck attributes.

        :param abstract_syntax_tree: This is the abstract syntax tree that was generated by the parser
        :type abstract_syntax_tree: Tree
        """
        super().__init__()
        self.code = []
        self.ast = abstract_syntax_tree
        self.symbol_table = symbol_table
        self.curr_func_name = None

    def generate_instructions(self):
        """
        It generates instructions for the PL/0.
        """
        self.generate_instruction(inst(Inst.int), 0, 3)
        self.generate_code(sub_tree=self.clear_tree(self.ast.iter_prepostorder()), symbol_table=self.symbol_table)
        # end of code
        self.generate_instruction(inst(Inst.ret), 0, 0)

    def generate_instruction(self, inst_name, param1, param2):
        """
        It appends a list of three elements to the list called code

        :param inst_name: The name of the instruction
        :param param1: the first parameter of the instruction
        :param param2: the value of the second parameter
        """
        self.code.append([inst_name, param1, param2])

    def print_code(self, out_method):
        """
        It prints the code of the program
        """
        for index, c in enumerate(self.code):
            out_method(str(index) + " " + "" + str(c[0]) + " " + str(c[1]) + " " + str(c[2]))

    def print_symbol_table(self, out_method):
        """
        It prints the symbol table
        """
        for i in self.symbol_table.values():
            if i.type == "func":
                out_method(i.__str__())

                if i.params is not None:
                    out_method("--------params--------\n")
                    for j in i.params:
                        out_method(i.params[j].__str__())

                if i.locals is not None:
                    out_method("--------locals--------\n")
                    for k in i.locals:
                        out_method(i.locals[k].__str__())
            else:
                out_method(i.__str__())

    def return_code(self) -> str:
        """
        This function returns a string of the code in the format of "index opcode operand1 operand2"
        :return: The return_code method returns a string of the code.
        """
        code_string = ""
        for index, c in enumerate(self.code):
            code_string += (str(index) + " " + str(c[0]) + " " + str(c[1]) + " " + str(c[2]) + "\n")
        return code_string

    def generate_code(self, sub_tree=None, level=0, symbol_table=None):
        """
        It generates code for the PL/0 compiler
        :param sub_tree: The current node of the tree that we are generating code for
        :param level: the level of the current node in the tree, defaults to 0 (optional)
        :param symbol_table: a dictionary that maps variable names to their values
        """
        sub_tree = list(sub_tree)
        index = 0
        while index < len(sub_tree):
            #  generates expression_term statements
            if sub_tree[index].name in self.expressions:
                index = self.gen_expression(sub_tree, index, symbol_table=symbol_table, level=level)
            #  generates variable declaration statements
            elif sub_tree[index].name == "var_declaration_expression":
                index, level = self.gen_var_declaration_expression(sub_tree, index, level=level,
                                                                   symbol_table=symbol_table)
            #  generates variable modification statements
            elif sub_tree[index].name in self.var_modifications:
                self.var_modifications[sub_tree[index].name](sub_tree[index].name)

            elif sub_tree[index].name == "var_modification":
                index, level = self.gen_var_modification(sub_tree, index, level, symbol_table=symbol_table)
            #  generates if (else) statements
            elif sub_tree[index].name == "if_stmt" or sub_tree[index].name == "if_else_stmt":
                index, level = self.gen_if_else(sub_tree, index, level, symbol_table=symbol_table)
            elif sub_tree[index].name == "function_signature":
                index, level = self.gen_function_signature(sub_tree, index, level=level,
                                                           symbol_table=symbol_table)
            #  update index
            index += 1

    def gen_function_signature(self, sub_tree, index, symbol_table=None, level=0):
        """
        This function generates the function signature adn body for a function definition

        :param sub_tree: the subtree of the AST that we're currently working on
        :param index: the index of the current node in the tree
        :param symbol_table: The symbol table that the function is being added to
        :param level: the level of the function in the tree, defaults to 0 (optional)
        """
        self.curr_func_name = sub_tree[index].children[0].name
        y = id("y" + str(self.curr_func_name))
        self.generate_instruction(inst(Inst.jmp), 0, y)
        self.symbol_table[self.curr_func_name].address = len(self.code)
        func_block = sub_tree[index].children[3].children[0]
        sub_sub_tree = self.clear_tree(func_block.iter_prepostorder())
        index += len(self.clear_tree(sub_tree[index].iter_prepostorder())) - len(sub_sub_tree)
        locals_and_params = {}
        if symbol_table[self.curr_func_name].locals is not None:
            locals_and_params.update(symbol_table[self.curr_func_name].locals)
        if symbol_table[self.curr_func_name].params is not None:
            locals_and_params.update(symbol_table[self.curr_func_name].params)
        for new_addr, i in enumerate(locals_and_params.values()):
            i.level = level + 1
            i.address = new_addr + 3
        self.generate_instruction(inst(Inst.int), 0, 3 + len(symbol_table[self.curr_func_name].params))
        self.generate_instruction(inst(Inst.lod), 0, - len(symbol_table[self.curr_func_name].params))
        self.generate_code(sub_tree=sub_sub_tree, level=level,
                           symbol_table=locals_and_params)
        index += len(sub_sub_tree)
        self.generate_instruction(inst(Inst.sto), 0, 1 - (len(symbol_table[self.curr_func_name].params)))
        self.generate_instruction(inst(Inst.ret), 0, 0)
        for i in self.code:
            if i[2] == y:
                i[2] = len(self.code)
        return index, level

    def gen_var_declaration_expression(self, sub_tree, index, symbol_table=None, level=0):
        """
        It generates a variable declaration expression.

        :param sub_tree: the subtree of the AST that we're currently working on
        :param index: the index of the current node in the tree
        :param symbol_table: the symbol table that the variable is being declared in
        :param level: the level of the current scope, defaults to 0 (optional)
        """
        self.generate_instruction(inst(Inst.int), 0, 1)
        sub_sub_tree = self.clear_tree(sub_tree[index].children[2].iter_prepostorder())
        # shifting index to skip duplicates
        # recursive call
        self.generate_code(sub_tree=sub_sub_tree, level=level, symbol_table=symbol_table)
        self.store_var(symbol_table[sub_tree[index].children[0].name])
        index += len(sub_sub_tree)
        return index, level

    def gen_const(self, const):
        """
        It generates a constant
        :param const: The constant to be generated
        """
        if type(const) == int:
            self.generate_instruction(inst(Inst.lit), 0, const)

    def gen_opr(self, const1, operator: Op, const2):
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
        self.generate_instruction(inst(Inst.opr), 0, str(operator))

    @staticmethod
    def clear_tree(tree_iter_generator):
        """
        It takes a generator that yields tree iterators, and clears the tree of all rows
        :param tree_iter_generator: A generator that returns a Gtk.TreeIter for each row in the tree
        """
        sub_tree = []
        for i in tree_iter_generator:
            if not i[0]:
                sub_tree.append(i[1])
        return sub_tree

    def gen_condition(self, condition, index, level, symbol_table=None):
        """
        It generates a condition
        for a given index and level

        :param condition: the condition to be generated
        :param index: the index of the current node in the AST
        :param level: the level of indentation
        :param symbol_table: a dictionary of the form {'var_name': 'var_type'}
        """
        index += 2
        index, level = self.generate_code_again(index, level, symbol_table, condition.children[0])
        index, level = self.generate_code_again(index, level, symbol_table, condition.children[2])
        self.cond_expressions[condition.children[1].get_leaf_names()[0]]()
        return condition, index, level

    def gen_func_call(self, sub_tree, symbol_table=None, level=0):
        """
        It generates the code for a function call

        :param sub_tree: The subtree of the AST that represents the function call
        :param symbol_table: The symbol table that the function is being called in
        :param level: the level of indentation, defaults to 0 (optional)
        """
        i = 0
        func_len = 0

        while i < (len(sub_tree)):
            if sub_tree[i].name == "function_call":
                sub_sub_tree = self.clear_tree(sub_tree[i].iter_prepostorder())
                self.generate_instruction(inst(Inst.int), 0, 1)
                f_name = sub_tree[i].children[0].name
                f_args = sub_tree[i].children[1]
                args_len = 0
                while f_args.name == "arguments_list":
                    if f_args.children[0].get_leaf_names()[0] in symbol_table.keys():
                        self.gen_load_symbol(symbol_table[f_args.children[0].get_leaf_names()[0]])
                        args_len += 1
                    else:
                        self.gen_const(f_args.children[0].get_leaf_names()[0])
                        args_len += 1
                    f_args = copy(f_args.children[1])

                if f_args.children[0].get_leaf_names()[0] in symbol_table.keys():
                    self.gen_load_symbol(symbol_table[f_args.children[0].get_leaf_names()[0]])
                    args_len += 1
                elif f_args.children[0].get_leaf_names()[0] != "":
                    self.gen_const(f_args.children[0].get_leaf_names()[0])
                    args_len += 1
                i += len(sub_sub_tree)
                func_len = i
                self.generate_instruction(inst(Inst.cal), level, symbol_table[f_name].address)
                if args_len > 0:
                    self.generate_instruction(inst(Inst.int), 0, -args_len)
            i += 1
        if func_len > 0:
            return i
        else:
            return None

    def gen_expression(self, sub_tree, index, symbol_table=None, level=0):
        """
        It takes a tree, an index, and a symbol table, and returns a string of Python code

        :param level: level
        :param sub_tree: The subtree of the parse tree that we are currently working on
        :param index: the index of the current node in the tree
        :param symbol_table: a dictionary of variables and their values
        """

        func_len = self.gen_func_call(sub_tree, symbol_table=symbol_table, level=level)
        if func_len is not None:
            return func_len

        leaf_names = sub_tree[index].get_leaf_names()
        leaves = sub_tree[index].get_leaves()
        if len(leaf_names) > 2:
            sub_sub_tree = sub_tree[0].get_common_ancestor(leaves[0], leaves[1])
            # shifting index to skip duplicates
            # recursive call
            index = self.gen_expression(sub_tree=self.clear_tree(sub_sub_tree.iter_prepostorder()), index=index,
                                        symbol_table=symbol_table)
            for i in range(2, len(leaf_names)):
                if leaf_names[i] in symbol_table.keys():
                    self.gen_load_symbol(symbol_table[leaf_names[i]])
                parent = sub_tree[0].get_common_ancestor(sub_sub_tree, leaves[i])
                self.expressions[parent.name](leaf_names[i])
            index += len(sub_tree)

        elif sub_tree[index].name == "expression_term":
            self.expressions[sub_tree[index].name](leaf_names[0])
        elif leaf_names[0] in symbol_table.keys() and leaf_names[1] in symbol_table.keys():
            self.expressions[sub_tree[index].name]()
            index += 2
        elif leaf_names[0] in symbol_table.keys():
            self.gen_load_symbol(symbol_table[leaf_names[0]])
            self.expressions[sub_tree[index].name](leaf_names[1])
            index += 1
        elif leaf_names[1] in symbol_table.keys():
            self.gen_load_symbol(symbol_table[leaf_names[1]])
            self.expressions[sub_tree[index].name](leaf_names[0])
            index += 1
        else:
            self.expressions[sub_tree[index].name](leaf_names[0], leaf_names[1])
            index += 2
        return index

    def gen_var_modification(self, sub_tree, index, level, symbol_table=None):
        """
         This function generates a variable modification statement

        :param sub_tree: The subtree of the AST that we are currently working on
        :param index: the index of the current node in the tree
        :param level: the level of the current scope
        :param symbol_table: a dictionary of the form {'var_name': 'var_type'}
        """
        symbol_name = sub_tree[index].children[0].name
        oper_and_equals = sub_tree[index].children[1]
        index, level = self.generate_code_again(index, level, symbol_table, sub_tree[index].children[2])
        if oper_and_equals.name != "=":
            self.gen_load_symbol(symbol_table[symbol_name])
        # shifting index to skip duplicates
        # recursive call
        self.generate_code(sub_tree=oper_and_equals, level=level + 1)

        index += 1
        self.store_var(symbol_table[symbol_name])
        return index, level

    def gen_if_else(self, sub_tree, index, level, symbol_table=None):
        """
        It generates the code for an if-else statement

        :param sub_tree: The subtree of the AST that we are currently working on
        :param index: the index of the current node in the tree
        :param level: the level of indentation
        :param symbol_table: The symbol table that is passed down from the parent node
        """
        condition = sub_tree[index].children[0]
        block1 = sub_tree[index].children[1]
        block2 = None
        if sub_tree[index].name == "if_else_stmt":
            block2 = sub_tree[index].children[2]
        if condition.children[1].get_leaf_names()[0] in self.cond_expressions:
            _, index, level = self.gen_condition(condition, index, level)
            # block 1
            sub_sub_tree = self.clear_tree(block1.children[0].iter_prepostorder())
            # shifting index to skip duplicates
            # recursive call
            x = id("x" + str(level))
            self.generate_instruction(inst(Inst.jmc), 0, x)
            self.generate_code(sub_tree=sub_sub_tree, level=level + 1, symbol_table=symbol_table)

            index += len(sub_sub_tree)
            for i in self.code:
                if i[2] == x:
                    jmc_address = len(self.code)
                    if block2 is not None:
                        jmc_address += 1
                    i[2] = jmc_address
            if block2 is not None:
                # block 2
                sub_sub_tree = self.clear_tree(block2.children[0].iter_prepostorder())
                # shifting index to skip duplicates
                # recursive call
                y = id("y" + str(level))
                self.generate_instruction(inst(Inst.jmp), 0, y)
                self.generate_code(sub_tree=sub_sub_tree, level=level + 1, symbol_table=symbol_table)

                index += len(sub_sub_tree)
                for i in self.code:
                    if i[2] == y:
                        i[2] = len(self.code)
        return index, level

    def generate_code_again(self, index, level, symbol_table, sub_tree):
        """
        It generates the code for the given node and its children

        :param index: the index of the current node in the tree
        :param level: the level of the current node in the tree
        :param symbol_table: a dictionary that maps variable names to their values
        :param sub_tree: the subtree of the AST that we are currently generating code for
        """
        sub_sub_tree = self.clear_tree(sub_tree.iter_prepostorder())
        # shifting index to skip duplicates
        # recursive call
        self.generate_code(sub_tree=sub_sub_tree, level=level, symbol_table=symbol_table)

        index += len(sub_sub_tree)
        return index, level

    def store_var(self, var: SymbolRecord):
        """
        Store a variable in the current scope.

        :param var: The variable to store
        :type var: SymbolRecord
        """
        self.generate_instruction(inst(Inst.sto), var.level, var.address)

    def gen_load_symbol(self, symbol: SymbolRecord):
        """
        It generates the code to load a symbol from the symbol table

        :param symbol: The symbol record for the symbol to be loaded
        :type symbol: SymbolRecord
        """
        self.generate_instruction(inst(Inst.lod), symbol.level, symbol.address)

    def gen_opr_add(self, const1=None, const2=None):
        self.gen_opr(const1, op(Op.add), const2)

    def gen_opr_sub(self, const1=None, const2=None):
        self.gen_opr(const1, op(Op.sub), const2)

    def gen_opr_mul(self, const1=None, const2=None):
        self.gen_opr(const1, op(Op.mul), const2)

    def gen_opr_div(self, const1=None, const2=None):
        self.gen_opr(const1, op(Op.div), const2)

    def gen_term(self, const1=None, const2=None):
        self.gen_const(const1)

    def gen_sub(self, operator):
        self.generate_instruction(inst(Inst.opr), 0, op(Op.sub))

    def gen_add(self, operator):
        self.generate_instruction(inst(Inst.opr), 0, op(Op.add))

    def gen_mulby(self, operator):
        self.generate_instruction(inst(Inst.opr), 0, op(Op.mul))

    def gen_divby(self, operator):
        self.generate_instruction(inst(Inst.opr), 0, op(Op.div))

    def gen_equals(self, operator):
        pass

    def gen_lesser(self):
        self.generate_instruction(inst(Inst.opr), 0, op(Op.lt))

    def gen_not_equal(self):
        self.generate_instruction(inst(Inst.opr), 0, op(Op.ne))

    def gen_lesser_equals(self):
        self.generate_instruction(inst(Inst.opr), 0, op(Op.le))

    def gen_greater(self):
        self.generate_instruction(inst(Inst.opr), 0, op(Op.gt))

    def gen_greater_equals(self):
        self.generate_instruction(inst(Inst.opr), 0, op(Op.ge))

    def gen_dos_equals(self):
        self.generate_instruction(inst(Inst.opr), 0, op(Op.eq))
