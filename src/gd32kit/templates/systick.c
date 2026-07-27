/*!
    \file    systick.c
    \brief   systick driver
*/

#include "gd32f527.h"
#include "systick.h"

volatile static uint32_t delay_time;

void systick_config(void)
{
    /* setup systick timer for 1000Hz interrupts */
    if (SysTick_Config(SystemCoreClock / 1000U)){
        /* capture error */
        while (1){
        }
    }
    /* configure the systick handler priority */
    NVIC_SetPriority(SysTick_IRQn, 0x00U);
}

void delay_1ms(uint32_t count)
{
    delay_time = count;

    while(0U != delay_time){
    }
}

void delay_decrement(void)
{
    if (0U != delay_time){
        delay_time--;
    }
}
