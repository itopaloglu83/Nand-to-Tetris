// File: Mult.asm
// -----
// Author: Ihsan TOPALOGLU (itopaloglu83@gmail.com)
// Date: 23 May 2020
// Course: Nand to Tetris, Part 1
// 
// Summary: Multiplies two numbers.
// 

// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

// Put your code here.

// R2 = 0
@R2
M=0

(LOOP)
// if R1 == 0 goto END
@R1
D=M
@END
D;JEQ

// R2 = R2 + R0
@R0
D=M
@R2
M=D+M

// R1 = R1 - 1
@R1
M=M-1

// Goto LOOP
@LOOP
0;JMP

// Program Ends.
(END)
@END
0;JMP
