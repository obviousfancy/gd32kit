# gd32kit

Toolkit CLI para proyectos GD32F527 con el flujo Makefile +
arm-none-eabi-gcc + OpenOCD (sin Keil/IAR). El comando base es `gd32kit`;
cada accion es un subcomando (por ahora solo `new`, con mas por venir).

## Instalacion

```bash
pip install gd32kit
```

## Uso

```bash
gd32kit new
```

Genera un proyecto autocontenido (Makefile, `main.c`, linker script,
manejadores de interrupcion, systick y la configuracion de OpenOCD/flasheo
por SWD) listo para `make && make flash`, tomando el SDK
(`Firmware/` + `CMSIS_6/`) desde el repo
[gd32f527xx](https://github.com/Cesarbautista10/gd32f527xx).

El CLI pregunta el nombre del proyecto, una descripcion breve, que
perifericos vas a usar (GPIO siempre esta incluido) y donde crear la
carpeta. Genera:

```
mi_proyecto/
├── Makefile
├── main.c
├── gd32f527_it.c / .h
├── gd32f527_libopt.h
├── gd32f527_flash.ld
├── systick.c / .h
├── openocd_gd32f527.cfg
├── openocd_flash.cfg
├── fmc_prog.c
└── .gitignore
```

## Requisito: el SDK gd32f527xx

El Makefile generado busca el SDK (`Firmware/` y el submodulo `CMSIS_6/`)
en `$GD32_SDK_ROOT`, con `~/Documents/obviousfancy/gd32f527xx` como valor
por defecto. Si tu copia esta en otro lado:

```bash
export GD32_SDK_ROOT=/ruta/a/gd32f527xx
```

o por invocacion:

```bash
make GD32_SDK_ROOT=/ruta/a/gd32f527xx
```

## Por que existe `fmc_prog.c`

Este chip (GD32F527) no se deja flashear por las vias usuales: ni pyOCD
con el algoritmo generico `cortex_m`, ni el `.FLM` oficial de GigaDevice
via pyOCD, escriben la flash de verdad en este setup. La solucion es
`fmc_prog.c`: una rutina que se carga en RAM y el propio CPU ejecuta via
OpenOCD para hacer unlock/erase/program. `make flash` automatiza todo el
proceso.

## Desarrollo local

```bash
git clone <este-repo>
cd gd32kit
pip install -e .
gd32kit new
```
