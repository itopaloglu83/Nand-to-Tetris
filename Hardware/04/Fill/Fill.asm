// File: Fill.asm
// -----
// Author: Ihsan TOPALOGLU (itopaloglu83@gmail.com)
// Date: 23 May 2020
// Course: Nand to Tetris, Part 1
// 
// Summary: Checks for keyboard input and paints the screen accordingly.
// 

// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.

(KEYBOARD)

// fill = 0000.0000 0000.0000
@fill
M=0

// if KBD != 0 goto PAINT
@KBD
D=M
@PAINT
D;JEQ

// fill = 1111.1111 1111.1111
@fill
M=-1

(PAINT)

// address = SCREEN
@SCREEN
D=A
@address
M=D

(LOOP)
// if address == 24576 goto KEYBOARD
// SCREEN + SCREENSIZE = 24576
@address
D=M
@24576
D=D-A
@KEYBOARD
D;JEQ

// @address = fill
@fill
D=M
@address
A=M
M=D

// address = address + 1
@address
M=M+1

// goto LOOP
@LOOP
0;JMP
