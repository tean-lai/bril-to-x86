; hello_world.asm
;
; Author: Tean Lai
; Date:   2025-05-10


section .data
    message db "Hello World!", 0xA
    message_length equ $ - message

section .text
    global _start

_start:
    mov     rax, 1              ; syscall number for write
    mov     rdi, 1              ; file descriptor: stdout
    mov     rsi, message        ; pointer to message
    mov     rdx, message_length; length of message
    syscall                     ; make syscall

    ; Exit syscall
    mov     rax, 60             ; syscall number for exit
    xor     rdi, rdi            ; exit code 0
    syscall
