    @2
    D=A
    @i
    M=D        // i = 2

    @sum
    M=0        // sum = 0

(LOOP)
    @i
    D=M
    @50
    D=D-A
    @END
    D;JGT      // If i > 50, goto END

    @i
    D=M        // D = i
    @sum
    M=D+M      // sum = sum + i

    @i
    D=M
    @2
    D=D+A      // increment by 2

    @i
    M=D        // Store i = i + 2

    @LOOP
    0;JMP      // Repeat loop

(END)
    @END
