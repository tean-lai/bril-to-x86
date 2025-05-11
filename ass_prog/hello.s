; hello.asm
; A minimal Mach-O x86_64 program that writes "Hello, world!" to stdout

section .data
    msg     db      "Hello, world!", 0x0A    ; the string plus newline
    len     equ     $ - msg                   ; length of the string

section .text
    global _start                             ; entry point for the linker

_start:
    ; write(1, msg, len)
    mov     rax, 0x2000004    ; syscall number for write on macOS
    mov     rdi, 1            ; file descriptor 1 = stdout
    lea     rsi, [rel msg]    ; address of our message
    mov     rdx, len          ; length of the message
    syscall
