# File: VMTranslator.py
# -----
# Author: Ihsan TOPALOGLU (itopaloglu83@gmail.com)
# Date: 30 May 2020
# Course: Nand to Tetris, Part 2
# Project: 7
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
        else:
            # C_LABEL
            # C_GOTO
            # C_IF
            # C_FUNCTION
            # C_RETURN
            # C_CALL
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
        # Store file name for static label references.
        self.file_name = file_name[:-4]
        # Open the output file for writing.
        self.file = open(file_name, "w")
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

    def comment(self, command: str):
        """Writes to the output file the current command as a comment."""
        print("// " + command, file=self.file)

    def write_arithmetic(self, command: str):
        """Writes to the output file the arithmetic assembly code for the given command."""
        # print("write_arithmetic:", command)
        # arithmetic_commands = ["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"]
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

        # Add an empty line for debug purposes.
        output.append("")

        # Print assembly commands to the screen.
        for line in output:
            print(line, file=self.file)

    def write_push_pop(self, command: str, segment: str, index: int):
        """Writes to the output file the given push or pop command."""
        # print("write_push_pop:", command, segment, index)
        # segments = constant, local, argument, this, and that.
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

        # Add an empty line for debug purposes.
        output.append("")

        # Print assembly commands to the screen.
        for line in output:
            print(line, file=self.file)

    def close(self):
        """Closes the output file."""
        self.file.close()


def main():
    """Arranges the parsing and code conversion of a Virtual Machine file."""

    # Check if a file name is given.
    if len(sys.argv) != 2 or sys.argv[1][-3:] != ".vm":
        print("Error: Please provide a Virtual Machine file.")
        print("Usage: python " + os.path.basename(__file__) + " [file.vm]")
        return

    # Define input and output file names.
    input_file_name = sys.argv[1]
    output_file_name = sys.argv[1][:-3] + ".asm"

    # Create a parser with the input file.
    parser = Parser(input_file_name)

    # Create a code writer with the output file.
    code_writer = CodeWriter(output_file_name)

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
            argument1 = parser.arg1()
            argument2 = parser.arg2()
            code_writer.write_push_pop(command_type, argument1, argument2)
        else:
            raise NameError("Unsupported Command Type")

    # Close the output file before exiting.
    code_writer.close()


if __name__ == "__main__":
    main()
