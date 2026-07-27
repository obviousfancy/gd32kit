#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║                  gd32kit — CLI                       ║
║        GD32F527 Makefile+OpenOCD Toolkit             ║
║              Obviousfancy Lab                        ║
╚══════════════════════════════════════════════════════╝

Uso:
    gd32kit new
"""

import argparse
import os
import re
import sys
from datetime import date
from importlib import resources
from pathlib import Path

try:
    import questionary
    from questionary import Style
except ImportError:
    print("[ERROR] Falta instalar questionary:")
    print("        pip install questionary")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────
# CONFIGURACION GLOBAL
# ─────────────────────────────────────────────────────────────

TEMPLATES_PKG = "gd32kit.templates"

# Archivos que se copian tal cual (no dependen de la seleccion del usuario).
STATIC_FILES = [
    "gd32f527_it.c",
    "gd32f527_it.h",
    "gd32f527_libopt.h",
    "gd32f527_flash.ld",
    "systick.c",
    "systick.h",
    "openocd_gd32f527.cfg",
    "openocd_flash.cfg",
    "fmc_prog.c",
]

# ─────────────────────────────────────────────────────────────
# MAPA DE PERIFERICOS
# Cada entrada define:
#   - source:   archivo .c del SDK (Firmware/GD32F527_standard_peripheral/Source/)
#               que se agrega al Makefile, o None si no hace falta nada extra
#   - init:     snippet de ejemplo (comentado) que se agrega a main()
#   - brief:    descripcion para el menu
# GPIO, RCU, MISC y SYSCFG siempre se compilan (son la base minima), por eso
# no aparecen en este mapa.
# ─────────────────────────────────────────────────────────────

PERIPHERALS = {
    "USART": {
        "source": "gd32f527_usart.c",
        "init": "    // usart_baudrate_set(USART0, 115200U);\n    // usart_enable(USART0);",
        "brief": "USART — Comunicacion serial asincrona",
    },
    "I2C": {
        "source": "gd32f527_i2c.c",
        "init": "    // i2c_clock_config(I2C0, 100000U, I2C_DTCY_2);\n    // i2c_enable(I2C0);",
        "brief": "I2C — Bus serial de 2 hilos (SDA/SCL)",
    },
    "SPI": {
        "source": "gd32f527_spi.c",
        "init": "    // spi_init(SPI0, &spi_parameter);\n    // spi_enable(SPI0);",
        "brief": "SPI — Bus serial de 4 hilos (SCK/MOSI/MISO/CS)",
    },
    "ADC": {
        "source": "gd32f527_adc.c",
        "init": "    // adc_mode_config(ADC_MODE_FREE);\n    // adc_enable(ADC0);",
        "brief": "ADC — Lectura analogica (conversor A/D)",
    },
    "DAC": {
        "source": "gd32f527_dac.c",
        "init": "    // dac_deinit();\n    // dac_enable(DAC0);",
        "brief": "DAC — Salida analogica (conversor D/A)",
    },
    "TIMER": {
        "source": "gd32f527_timer.c",
        "init": "    // timer_init(TIMER0, &timer_parameter);\n    // timer_enable(TIMER0);",
        "brief": "TIMER — Temporizadores, PWM y captura de entrada",
    },
    "DMA": {
        "source": "gd32f527_dma.c",
        "init": "    // dma_single_data_mode_init(DMA0, DMA_CH0, &dma_parameter);\n    // dma_channel_enable(DMA0, DMA_CH0);",
        "brief": "DMA — Transferencias por acceso directo a memoria",
    },
    "EXTI": {
        "source": "gd32f527_exti.c",
        "init": "    // exti_init(EXTI_0, EXTI_INTERRUPT, EXTI_TRIG_FALLING);\n    // nvic_irq_enable(EXTI0_IRQn, 0U, 0U);",
        "brief": "EXTI — Interrupciones externas por pin",
    },
    "CAN": {
        "source": "gd32f527_can.c",
        "init": "    // can_init(CAN0, &can_parameter);",
        "brief": "CAN — Bus CAN",
    },
    "RTC": {
        "source": "gd32f527_rtc.c",
        "init": "    // rtc_init(&rtc_initpara);",
        "brief": "RTC — Reloj de tiempo real",
    },
}

CLI_STYLE = Style([
    ("qmark", "fg:#00d7af bold"),
    ("question", "fg:#ffffff bold"),
    ("answer", "fg:#00d7af bold"),
    ("pointer", "fg:#00d7af bold"),
    ("highlighted", "fg:#00d7af bold"),
    ("selected", "fg:#00d7af"),
    ("separator", "fg:#444444"),
    ("instruction", "fg:#888888"),
    ("text", "fg:#ffffff"),
    ("disabled", "fg:#444444 italic"),
])

# ─────────────────────────────────────────────────────────────
# VALIDACIONES
# ─────────────────────────────────────────────────────────────


def validate_project_name(name: str):
    if not name:
        return "El nombre no puede estar vacio"
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_]*$", name):
        return "Solo letras, numeros y guion bajo. Sin espacios. No puede empezar con guion bajo."
    return True


def validate_project_path(path: Path, project_name: str):
    if (path / project_name).exists():
        return f"Ya existe '{project_name}' en {path}"
    return True


# ─────────────────────────────────────────────────────────────
# GENERACION DE ARCHIVOS
# ─────────────────────────────────────────────────────────────


def read_template(name: str) -> str:
    return resources.files(TEMPLATES_PKG).joinpath(name).read_text()


def generate_makefile(project_name: str, selected: list[str]) -> str:
    template = read_template("Makefile.template")

    extra_sources = ""
    for p in selected:
        src = PERIPHERALS[p]["source"]
        extra_sources += f" \\\n$(PERIPH_DIR)/Source/{src}"

    return template.replace("{{TARGET}}", project_name).replace(
        "{{EXTRA_SOURCES}}", extra_sources
    )


def generate_main_c(brief: str, selected: list[str]) -> str:
    template = read_template("main.c.template")

    init_blocks = [PERIPHERALS[p]["init"] for p in selected if p in PERIPHERALS]
    init_code = ("\n".join(init_blocks) + "\n\n") if init_blocks else ""

    return (
        template.replace("{{PROJECT_BRIEF}}", brief)
        .replace("{{DATE}}", date.today().isoformat())
        .replace("{{INIT_CODE}}", init_code)
    )


def write_static_files(project_path: Path) -> None:
    for name in STATIC_FILES:
        content = read_template(name)
        (project_path / name).write_text(content)
    (project_path / ".gitignore").write_text(read_template("gitignore.template"))


# ─────────────────────────────────────────────────────────────
# COMANDO: gd32kit new
# ─────────────────────────────────────────────────────────────


def cmd_new(args):
    print("\n╔══════════════════════════════════════════════════════╗")
    print("║               gd32kit new — Scaffolding              ║")
    print("║   GD32F527 Makefile + OpenOCD Project Generator      ║")
    print("║              Obviousfancy Lab                        ║")
    print("╚══════════════════════════════════════════════════════╝\n")

    project_name = questionary.text(
        "Nombre del proyecto:",
        validate=validate_project_name,
        style=CLI_STYLE,
    ).ask()
    if project_name is None:
        print("\n[CANCELADO]")
        sys.exit(0)

    brief = questionary.text(
        "Descripcion breve del proyecto:",
        default=f"Proyecto {project_name} para GD32F527",
        style=CLI_STYLE,
    ).ask()
    if brief is None:
        print("\n[CANCELADO]")
        sys.exit(0)

    peripheral_choices = [
        questionary.Choice(title=PERIPHERALS[p]["brief"], value=p)
        for p in PERIPHERALS
    ]
    selected_peripherals = questionary.checkbox(
        "Selecciona los perifericos que usaras (Space para marcar, Enter para confirmar):",
        choices=peripheral_choices,
        style=CLI_STYLE,
    ).ask()
    if selected_peripherals is None:
        print("\n[CANCELADO]")
        sys.exit(0)

    default_path = str(Path.cwd())
    ruta_str = questionary.text(
        "Ruta donde crear el proyecto (Enter para usar la carpeta actual):",
        default=default_path,
        style=CLI_STYLE,
    ).ask()
    if ruta_str is None:
        print("\n[CANCELADO]")
        sys.exit(0)

    base_path = Path(ruta_str).expanduser().resolve()
    path_check = validate_project_path(base_path, project_name)
    if path_check is not True:
        print(f"\n[ERROR] {path_check}")
        sys.exit(1)

    project_path = base_path / project_name

    print(f"\n  Proyecto   : {project_name}")
    print(f"  Perifericos: {', '.join(selected_peripherals) if selected_peripherals else 'ninguno (solo GPIO)'}")
    print(f"  Destino    : {project_path}\n")

    confirm = questionary.confirm("Crear el proyecto?", default=True, style=CLI_STYLE).ask()
    if not confirm:
        print("\n[CANCELADO]")
        sys.exit(0)

    project_path.mkdir(parents=True, exist_ok=False)

    (project_path / "Makefile").write_text(generate_makefile(project_name, selected_peripherals))
    (project_path / "main.c").write_text(generate_main_c(brief, selected_peripherals))
    write_static_files(project_path)

    print(f"\n  ✓ {project_path / 'Makefile'}")
    print(f"  ✓ {project_path / 'main.c'}")
    for name in STATIC_FILES:
        print(f"  ✓ {project_path / name}")
    print(f"  ✓ {project_path / '.gitignore'}")

    sdk_root = os.environ.get(
        "GD32_SDK_ROOT", str(Path.home() / "Documents/obviousfancy/gd32f527xx")
    )

    print(f"\n╔══════════════════════════════════════════════════╗")
    print(f"║  Proyecto '{project_name}' creado correctamente")
    print(f"╚══════════════════════════════════════════════════╝")
    print(f"\n  SDK usado (Firmware/ + CMSIS_6/): {sdk_root}")
    print(f"  (si no es correcto: export GD32_SDK_ROOT=/ruta/a/gd32f527xx, o")
    print(f"   pasalo por invocacion: make GD32_SDK_ROOT=/ruta/a/gd32f527xx)")
    print(f"\n  Para compilar y flashear:")
    print(f"    cd {project_path}")
    print(f"    make")
    print(f"    make flash\n")


# ─────────────────────────────────────────────────────────────
# DISPATCHER
# ─────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gd32kit",
        description="Toolkit para proyectos GD32F527 (Makefile + arm-none-eabi-gcc + OpenOCD, sin Keil/IAR).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("new", help="Crea un proyecto nuevo de forma interactiva").set_defaults(func=cmd_new)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
