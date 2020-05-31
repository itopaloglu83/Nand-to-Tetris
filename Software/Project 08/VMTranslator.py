# File: VMTranslator.py
# -----
# Author: Ihsan TOPALOGLU (itopaloglu83@gmail.com)
# Date: 31 May 2020
# Course: Nand to Tetris, Part 2
# Project: 8
#
# Summary: Virtual Machine Translator that takes a .vm file and creates a .asm file.
#

import os
import sys


class Parser:
    """Hack File Parser

    Loads the given VM file and provides helper functions to parse the commands.
    """

    def __init__(self, file_name: str):
        """Opens the file and prepares for parsing."""
        # Current command that's being processed.
        self.current_command = ""
        # Current command index.
        self.current = -1
        # All commands from the input file.
        self.commands = []
        # Open the file and prepare for parsing.
        # Remove all comments, empty lines, and whitespace characters.
        file = open(file_name)
        for line in file:
            line = line.partition("//")[0]
            line = line.strip()
            if line:
                self.commands.append(line)
        file.close()

    def hasMoreCommands(self) -> bool:
        """Checks if there are any more commands."""
        return (self.current + 1) < len(self.commands)

    def advance(self) -> None:
        """Reads the next command and makes it the current command."""
        self.current += 1
        self.current_command = self.commands[self.current]

    def commandType(self) -> str:
        """Returns the type of the current command."""
        # Define the list of known arithmetic commands.
        arithmetic_commands = ["add", "sub", "neg",
                               "eq", "gt", "lt", "and", "or", "not"]
        # Extract the current command from the input line.
        cmd = self.current_command.split(" ")[0]
        # Determine the type of the current command.
        if cmd in arithmetic_commands:
            return "C_ARITHMETIC"
        elif cmd == "push":
            return "C_PUSH"
        elif cmd == "pop":
            return "C_POP"
        elif cmd == "label":
            return "C_LABEL"
        elif cmd == "goto":
            return "C_GOTO"
        elif cmd == "if-goto":
            return "C_IF"
        elif cmd == "function":
            return "C_FUNCTION"
        elif cmd == "call":
            return "C_CALL"
        elif cmd == "return":
            return "C_RETURN"
        else:
            raise NameError("Unexpected Command Type")

    def arg1(self) -> str:
        """Returns the first argument of the current command. For C_ARITHMETIC returns the command itself. Should not be called for C_RETURN."""
        if self.commandType() == "C_ARITHMETIC":
            return self.current_command.split(" ")[0]
        else:
            return self.current_command.split(" ")[1]

    def arg2(self) -> int:
        """Returns the second argument of the current command. Only valid for C_PUSH, C_POP, C_FUNCTION, and C_RETURN."""
        return int(self.current_command.split(" ")[2])


class CodeWriter:
    """VM Code Converter

    Converts the VM commands to assembly code and writes them into output file.
    """

    def __init__(self, file_name: str):
        """Setups the code converter for the given output file."""
        # Open the output file for writing.
        self.file = open(file_name, "w")
        # Store the file name for static label references.
        self.file_name = ""
        # Store the function name for label references.
        self.function_name = "OS"
        # Create a label counter for unique label creation.
        self.label_counter = 0
        # Symbols table for arithmetic operations and assembly symbols.
        self.symbols = {
            # Arithmetic Operators
            "add": "M=D+M",
            "sub": "M=M-D",
            "and": "M=D&M",
            "or": "M=D|M",
            "neg": "M=-M",
            "not": "M=!M",
            "eq": "D;JEQ",
            "gt": "D;JGT",
            "lt": "D;JLT",
            # Assembly Symbols
            "local": "@LCL",
            "argument": "@ARG",
            "this": "@THIS",
            "that": "@THAT",
            "constant": "",
            "static": "",
            "pointer": "@3",
            "temp": "@5"
        }

    def write_init(self):
        """Writes the VM bootstrap code."""
        output = []
        # Initialize the Stack Pointer.
        output.append("@256")
        output.append("D=A")
        output.append("@SP")
        output.append("M=D")
        self.write_to_file(output)
        # Define OS Function.
        self.write_function("OS", 0)
        # Call Sys.init for runtime.
        self.write_call("Sys.init", 0)

    def set_file_name(self, file_name: str):
        """Informs the codewriter about the file being processed."""
        self.file_name = file_name

    def comment(self, input: str):
        """Writes a comment with the given input."""
        self.write_to_file(["// " + input], False)

    def write_arithmetic(self, command: str):
        """Writes the assembly code for a given arithmetic vm command."""
        output = []
        if command in ["add", "sub", "and", "or"]:
            # Pop Stack into D.
            output.append("@SP")
            output.append("AM=M-1")
            output.append("D=M")
            # Access to Stack[-1]
            output.append("@SP")
            output.append("A=M-1")
            # Use the Arithmetic Operator
            output.append(self.symbols[command])
        elif command in ["neg", "not"]:
            # Access to Stack[-1]
            output.append("@SP")
            output.append("A=M-1")
            output.append(self.symbols[command])
        elif command in ["eq", "gt", "lt"]:
            jump_label = "CompLabel" + str(self.label_counter)
            self.label_counter += 1
            # Pop Stack into D.
            output.append("@SP")
            output.append("AM=M-1")
            output.append("D=M")
            # Access to Stack[-1]
            output.append("@SP")
            output.append("A=M-1")
            # Calculate the difference
            output.append("D=M-D")
            # Set the Stack to True in anticipation.
            output.append("M=-1")
            # Load the jump label into A.
            output.append("@" + jump_label)
            # Jump if the statement is True.
            # Else update the Stack to False.
            output.append(self.symbols[command])
            # Set the Stack[-1] to False
            output.append("@SP")
            output.append("A=M-1")
            output.append("M=0")
            # Jump label for the True state.
            output.append("(" + jump_label + ")")
        else:
            raise NameError("Unexpected Arithmetic Command")

        # Print assembly commands.
        self.write_to_file(output)

    def write_push_pop(self, command: str, segment: str, index: int):
        """Writes the push and pop code for a given vm command."""
        output = []
        if command == "C_PUSH":
            if segment == "constant":
                output.append("@" + str(index))
                output.append("D=A")
                output.append("@SP")
                output.append("AM=M+1")
                output.append("A=A-1")
                output.append("M=D")
            elif segment in ["local", "argument", "this", "that", "temp", "pointer"]:
                # Put the index value into D.
                output.append("@" + str(index))
                output.append("D=A")
                # Put the base value into A.
                if segment == "temp" or segment == "pointer":
                    output.append(self.symbols[segment])
                else:
                    # Resolve where the segment refers to.
                    output.append(self.symbols[segment])
                    output.append("A=M")
                # Calculate the source address into A.
                output.append("A=D+A")
                # Put the source value into D.
                output.append("D=M")
                # Put D value into where SP points to.
                output.append("@SP")
                output.append("A=M")
                output.append("M=D")
                # Increment the stack pointer.
                output.append("@SP")
                output.append("M=M+1")
            elif segment == "static":
                # Calculate the source address into A.
                output.append("@" + self.file_name + "." + str(index))
                # Put the source value into D.
                output.append("D=M")
                # Put D value into where SP points to.
                output.append("@SP")
                output.append("A=M")
                output.append("M=D")
                # Increment the stack pointer.
                output.append("@SP")
                output.append("M=M+1")
            else:
                raise NameError("Unexpected Push Segment")
        elif command == "C_POP":
            if segment == "constant":
                # Not a valid command.
                raise NameError("Cannot Pop Constant Segment")
            elif segment in ["local", "argument", "this", "that", "temp", "pointer"]:
                # Put the index value into D.
                output.append("@" + str(index))
                output.append("D=A")
                # Put the base value into A.
                if segment == "temp" or segment == "pointer":
                    output.append(self.symbols[segment])
                else:
                    # Resolve where the segment refers to.
                    output.append(self.symbols[segment])
                    output.append("A=M")
                # Calculate the source address into D.
                output.append("D=D+A")
                # Put D value into R13 for future use.
                output.append("@R13")
                output.append("M=D")
                # Pop stack value into D.
                output.append("@SP")
                output.append("AM=M-1")
                output.append("D=M")
                # Put D value into where R13 points to.
                output.append("@R13")
                output.append("A=M")
                output.append("M=D")
            elif segment == "static":
                # Pop stack value into D.
                output.append("@SP")
                output.append("AM=M-1")
                output.append("D=M")
                # Put the source address into A.
                output.append("@" + self.file_name + "." + str(index))
                # Put D value into static address.
                output.append("M=D")
            else:
                raise NameError("Unexpected Pop Segment")
        else:
            raise NameError("Unexpected Command Type")

        # Print assembly commands.
        self.write_to_file(output)

    def write_label(self, label: str):
        """Writes the aseembly label."""
        label_name = self.function_name + "$" + label
        output = []
        output.append("(" + label_name + ")")
        self.write_to_file(output)

    def write_goto(self, label: str):
        """Writes unconditional jump to the given label."""
        label_name = self.function_name + "$" + label
        output = []
        output.append("@" + label_name)
        output.append("0;JMP")
        self.write_to_file(output)

    def write_if(self, label: str):
        """Writes conditional jump to the given label."""
        label_name = self.function_name + "$" + label
        output = []
        # Pop stack value into D.
        output.append("@SP")
        output.append("AM=M-1")
        output.append("D=M")
        # Jump to label if D is True
        # (Not Equal to 0)
        output.append("@" + label_name)
        output.append("D;JNE")
        self.write_to_file(output)

    def write_function(self, function_name: str, num_vars: int):
        """Writes the function definition in assembly."""
        output = []
        self.function_name = function_name
        output.append("(" + self.function_name + ")")
        self.write_to_file(output)
        for _ in range(num_vars):
            self.write_push_pop("C_PUSH", "constant", 0)

    def write_call(self, function_name: str, num_args: int):
        """Writes the necessary assembly code to call a function."""
        # Saves the current memory segments and initiates new ones for the called function.
        # return_label is created using the name of the caller function.
        # return_label = file_name.function_name$ret.i
        return_label = self.function_name + "$ret." + str(self.label_counter)
        self.label_counter += 1
        # Output stream is initiated.
        output = []
        # push return_label
        output.append("@" + return_label)
        output.append("D=A")
        output.append("@SP")
        output.append("A=M")
        output.append("M=D")
        output.append("@SP")
        output.append("M=M+1")
        # push LCL, ARG, THIS, and THAT
        for segment in ["LCL", "ARG", "THIS", "THAT"]:
            output.append("@" + segment)
            output.append("D=M")
            output.append("@SP")
            output.append("A=M")
            output.append("M=D")
            output.append("@SP")
            output.append("M=M+1")
        # ARG = SP -5 -num_args
        output.append("@SP")
        output.append("D=M")
        output.append("@5")
        output.append("D=D-A")
        output.append("@" + str(num_args))
        output.append("D=D-A")
        output.append("@ARG")
        output.append("M=D")
        # LCL = SP
        output.append("@SP")
        output.append("D=M")
        output.append("@LCL")
        output.append("M=D")
        # goto function_name
        output.append("@" + function_name)
        output.append("0;JMP")
        # (return_label)
        output.append("(" + return_label + ")")
        self.write_to_file(output)

    def write_return(self):
        """Writes the return code of a function call."""
        # Saves the return value and restores the previous call stack.
        # Output stream is initiated.
        output = []
        # frame_end = LCL
        # Store frame_end in R13.
        output.append("@LCL")
        output.append("D=M")
        output.append("@R13")
        output.append("M=D")
        # return_address = *(end_frame -5)
        # Store return address in R14.
        output.append("@5")
        output.append("A=D-A")
        output.append("D=M")
        output.append("@R14")
        output.append("M=D")
        # *ARG = pop()
        output.append("@SP")
        output.append("AM=M-1")
        output.append("D=M")
        output.append("@ARG")
        output.append("A=M")
        output.append("M=D")
        # SP = ARG +1
        output.append("@ARG")
        output.append("D=M+1")
        output.append("@SP")
        output.append("M=D")
        # Restore that, this, arg, and lcl segments.
        for segment in ["THAT", "THIS", "ARG", "LCL"]:
            output.append("@R13")
            output.append("AM=M-1")
            output.append("D=M")
            output.append("@" + segment)
            output.append("M=D")
        # goto return_address
        output.append("@R14")
        output.append("A=M")
        output.append("0;JMP")
        self.write_to_file(output)

    def write_to_file(self, output: list, new_line=True):
        """Writes a given list of output."""
        # Add an empty line for debug purposes.
        if new_line:
            output.append("")
        # Write every line to the output file.
        for line in output:
            print(line, file=self.file)

    def close(self):
        """Closes the output file."""
        self.file.close()


def main():
    """Arranges the parsing and code conversion of a Virtual Machine file."""

    # Check if an input file or a directory is given.
    if len(sys.argv) != 2:
        print("Error: No input file is found.")
        print("Usage: python " + __file__ + " [file.vm] | [directory]")
        return

    # Extract input files and setup the output file name.
    input_files = []
    input_path = sys.argv[1]
    # File name is given.
    if os.path.isfile(input_path) and input_path[-3:] == ".vm":
        input_files.append(input_path)
        output_file_name = input_path[:-3] + ".asm"
    # Directory name is given.
    elif os.path.isdir(input_path):
        # Remove trailing forward slash.
        if input_path[-1:] == "/":
            input_path = input_path[:-1]
        # List all .vm files.
        for file_name in os.listdir(input_path):
            if file_name[-3:] == ".vm":
                input_files.append(input_path + "/" + file_name)
        # Exit if no .vm file is found.
        if len(input_files) == 0:
            raise NameError("No Input File Found")
        output_file_name = input_path + ".asm"
    else:
        raise NameError("Unknown Input Path")

    # Create a code writer with the output file.
    code_writer = CodeWriter(output_file_name)

    # Insert the bootstrap code.
    code_writer.comment("Bootstrap Code")
    code_writer.write_init()

    # Loop over input files and translate them into one single assembly file.
    for input_file_name in input_files:
        # Set the file name for code writer.
        file_name = input_file_name.split("/")[-1][:-3]
        code_writer.set_file_name(file_name)

        # Create a parser with the input file.
        parser = Parser(input_file_name)

        # Scan the input file for VM commands and write translations to the output file.
        while parser.hasMoreCommands():
            parser.advance()
            # Write the current command as a comment to the output file for debugging purposes.
            code_writer.comment(parser.current_command)
            # Determine the current command type.
            # C_ARITHMETIC, C_PUSH, or C_POP.
            command_type = parser.commandType()
            if command_type == "C_ARITHMETIC":
                # Pass the arithmetic command to the code writer.
                code_writer.write_arithmetic(parser.arg1())
            elif command_type in ["C_PUSH", "C_POP"]:
                # Pass the push/pop command to the code writer with its arguments.
                segment = parser.arg1()
                index = parser.arg2()
                code_writer.write_push_pop(command_type, segment, index)
            elif command_type == "C_LABEL":
                # Define label.
                code_writer.write_label(parser.arg1())
            elif command_type == "C_GOTO":
                # Unconditional jump to label.
                code_writer.write_goto(parser.arg1())
            elif command_type == "C_IF":
                # Conditional jump to label.
                code_writer.write_if(parser.arg1())
            elif command_type == "C_FUNCTION":
                # Define a function with number of variables.
                function_name = parser.arg1()
                num_vars = parser.arg2()
                code_writer.write_function(function_name, num_vars)
            elif command_type == "C_CALL":
                # Call a function with number of arguments.
                function_name = parser.arg1()
                num_args = parser.arg2()
                code_writer.write_call(function_name, num_args)
            elif command_type == "C_RETURN":
                # Return from the current function.
                code_writer.write_return()
            else:
                raise NameError("Unsupported Command Type")

    # Close the output file before exiting.
    code_writer.close()


if __name__ == "__main__":
    main()
