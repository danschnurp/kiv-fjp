#  date: 8. 11. 2022
#  authors: Daniel Schnurpfeil,  Jiri Trefil
#
import os
from copy import copy

import ply.lex
import ply.yacc as yy

import src.syntax_analyzer as syntax
import src.lex_analyzer as lexical
import src.pl0_code_generator as gen
from src.semantics_analyzer.analyzer import Analyzer
from src.syntax_analyzer.symbol_table import generate_table_of_symbols


def generate_output_files(dst, generated_code, output_dir):
    """
    It generates output files

    :param dst: syntax tree
    :param generated_code: a list of strings, each of which is a line of generated code
    """
    if "output" not in os.listdir(output_dir):
        if output_dir[-1] != "/":
            output_dir += "/"
        os.mkdir(output_dir + "output")
    output_dir += "output"
    with open(output_dir + "/full_tree.txt", mode="w") as tree:
        tree.writelines(dst.get_ascii(attributes=["name", "dist", "label", "complex"]))
    with open(output_dir + "/tree.txt", mode="w") as tree:
        tree.writelines(str(dst))
    with open(output_dir + "/symbol_table.txt", mode="w") as table:
        generated_code.print_symbol_table(table.writelines)
    return output_dir


def visualize_dst(dst, show_tree_with_pyqt5):
    # # ###### Showing the tree. with pyqt5 ##################
    if show_tree_with_pyqt5:
        from ete3 import TreeStyle
        tree_style = TreeStyle()
        tree_style.show_leaf_name = True
        tree_style.mode = "c"
        tree_style.arc_start = -180  # 0 degrees = 3 o'clock
        dst.show(
            tree_style=tree_style
        )


def save_generated_code(generated_code, formatted_input_code, output_dir):
    """
    It saves the generated code to a file

    :param generated_code: The code that was generated by the model
    :param formatted_input_code: The input code, formatted with the correct indentation
    """
    if generated_code.return_code() != "":
        # Writing the generated code to a file.
        with open(output_dir + "/generated_code_with_input.txt", mode="w") as txt:
            txt.writelines("----------input code----------------\n")
            txt.writelines(formatted_input_code)
            txt.writelines("\n")
            txt.writelines("----------generated code------------\n")
            txt.writelines(generated_code.return_code())
            txt.writelines("------------------------------------")

        with open(output_dir + "/generated_code_only.txt", mode="w") as txt:
            txt.writelines(generated_code.return_code())


def main(input_file_name: str, output_dir="./",  show_tree_with_pyqt5=False):
    """
    > This function takes a file name as input, and returns a list of lists of strings

    :param input_file_name: The name of the file to be parsed
    :type input_file_name: str
    :param show_tree_with_pyqt5: If True, the tree will be displayed using PyQt5, defaults to False (optional)
    """

    with open(input_file_name) as f:
        code = f.read()
    formatted_input_code = copy(code)
    # Parsing the code_input.
    lexer = \
    ply.lex.lex(module=lexical)
    y = yy.yacc(module=syntax, debug=False, write_tables=False)
    dst = y.parse(formatted_input_code)
    if dst is None:
        raise Exception("Syntax error...")
    # Generating a table of symbols.
    table_of_symbols = {}
    generate_table_of_symbols(table_of_symbols, symbols=dst.get_leaves())

    #[JT] ZATIM NECHAVAM ZAKOMENTOVANO - JE TO HODNE SYROVE
    semantics_analyzer = Analyzer(dst, table_of_symbols)
    if not semantics_analyzer.Analyze():
        return


    generated_code = gen.Pl0(dst, table_of_symbols)

    # Generating the output files.
    output_dir = generate_output_files(dst, generated_code, output_dir)

    # Showing the tree.
    visualize_dst(dst, show_tree_with_pyqt5)

    # Generating the instructions for the PL/0 compiler.
    generated_code.generate_instructions()

    # Saving the generated code to a file.
    save_generated_code(generated_code, formatted_input_code, output_dir)

    return generated_code.return_code()


#main("../sample_input/not_tested/helloworld.swift")