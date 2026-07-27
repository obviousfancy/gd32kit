/*!
    \file    gd32f527_it.c
    \brief   interrupt service routines
*/

#include "gd32f527_it.h"
#include "systick.h"

void SysTick_Handler(void)
{
    delay_decrement();
}
