################################################################################
# Automatically-generated file. Do not edit!
################################################################################

-include ../makefile.init

RM := rm -rf

# All of the sources participating in the build are defined here
-include sources.mk
-include example/src/subdir.mk
ifneq ($(MAKECMDGOALS),clean)
ifneq ($(strip $(C_DEPS)),)
-include $(C_DEPS)
endif
endif

-include ../makefile.defs

OPTIONAL_TOOL_DEPS := \
$(wildcard ../makefile.defs) \
$(wildcard ../makefile.init) \
$(wildcard ../makefile.targets) \


BUILD_ARTIFACT_NAME := usbd_rom_hid_keyboard
BUILD_ARTIFACT_EXTENSION := axf
BUILD_ARTIFACT_PREFIX :=
BUILD_ARTIFACT := $(BUILD_ARTIFACT_PREFIX)$(BUILD_ARTIFACT_NAME)$(if $(BUILD_ARTIFACT_EXTENSION),.$(BUILD_ARTIFACT_EXTENSION),)

# Add inputs and outputs from these tool invocations to the build variables 

# All Target
all:
	+@$(MAKE) --no-print-directory main-build && $(MAKE) --no-print-directory post-build

# Main-build Target
main-build: usbd_rom_hid_keyboard.axf

# Tool invocations
usbd_rom_hid_keyboard.axf: $(OBJS) $(USER_OBJS) makefile $(OPTIONAL_TOOL_DEPS)
	@echo 'Building target: $@'
	@echo 'Invoking: MCU Linker'
	arm-none-eabi-gcc -nostdlib -L"D:\NXP\BP\LPC1549_USB_HID\lpc_chip_15xx\Debug" -L"D:\NXP\BP\LPC1549_USB_HID\lpc_board_nxp_lpcxpresso_1549\Debug" -Xlinker -Map="usbd_rom_hid_keyboard.map" -Xlinker --gc-sections -mcpu=cortex-m3 -mthumb -T usbd_rom_hid_keyboard_Debug.ld -o "usbd_rom_hid_keyboard.axf" $(OBJS) $(USER_OBJS) $(LIBS) -llpc_board_nxp_lpcxpresso_1549 -llpc_chip_15xx
	@echo 'Finished building target: $@'
	@echo ' '

# Other Targets
clean:
	-$(RM) usbd_rom_hid_keyboard.axf
	-@echo ' '

post-build:
	-@echo 'Performing post-build steps'
	-arm-none-eabi-size "usbd_rom_hid_keyboard.axf"; # arm-none-eabi-objcopy -v -O binary "usbd_rom_hid_keyboard.axf" "usbd_rom_hid_keyboard.bin" ; # checksum -p LPC1549 -d "usbd_rom_hid_keyboard.bin";
	-@echo ' '

.PHONY: all clean dependents main-build post-build

-include ../makefile.targets
