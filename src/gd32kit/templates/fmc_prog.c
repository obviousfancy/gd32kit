#include <stdint.h>

#define FMC_KEY  (*(volatile uint32_t *)0x40023C04)
#define FMC_STAT (*(volatile uint32_t *)0x40023C0C)
#define FMC_CTL  (*(volatile uint32_t *)0x40023C10)

#define FMC_STAT_BUSY    (1u << 16)
#define FMC_CTL_PG       (1u << 0)
#define FMC_CTL_MER0     (1u << 2)
#define FMC_CTL_MER1     (1u << 15)
#define FMC_CTL_START    (1u << 16)
#define FMC_CTL_PSZ_WORD (2u << 8)

static void fmc_wait(void)
{
    while (FMC_STAT & FMC_STAT_BUSY) {
    }
}

void flash_routine(uint32_t *dst, uint32_t *src, uint32_t count)
{
    FMC_KEY = 0x45670123;
    FMC_KEY = 0xCDEF89AB;

    /* mass erase: avoids needing the per-sector size table, works for any
     * binary size up to the chip's total flash capacity. */
    fmc_wait();
    FMC_CTL = FMC_CTL_MER0 | FMC_CTL_MER1;
    FMC_CTL = FMC_CTL_MER0 | FMC_CTL_MER1 | FMC_CTL_START;
    fmc_wait();
    FMC_CTL = 0;

    for (uint32_t i = 0; i < count; i++) {
        fmc_wait();
        FMC_CTL = FMC_CTL_PSZ_WORD | FMC_CTL_PG;
        dst[i] = src[i];
        fmc_wait();
        FMC_CTL = 0;
    }

    while (1) {
        __asm__ volatile("bkpt #0");
    }
}
