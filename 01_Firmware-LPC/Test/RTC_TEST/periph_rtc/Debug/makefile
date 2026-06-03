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


BUILD_ARTIFACT_NAME := periph_rtc
BUILD_ARTIFACT_EXTENSION := axf
BUILD_ARTIFACT_PREFIX :=
BUILD_ARTIFACT := $(BUILD_ARTIFACT_PREFIX)$(BUILD_ARTIFACT_NAME)$(if $(BUILD_ARTIFACT_EXTENSION),.$(BUILD_ARTIFACT_EXTENSION),)

# Add inputs and outputs from these tool invocations to the build variables 

# All Target
all:
	+@$(MAKE) --no-print-directory main-build && $(MAKE) --no-print-directory post-build

# Main-build Target
main-build: periph_rtc.axf

# Tool invocations
periph_rtc.axf: $(OBJS) $(USER_OBJS) makefile $(OPTIONAL_TOOL_DEPS)
	@echo 'Building target: $@'
	@echo 'Invoking: MCU Linker'
	arm-none-eabi-gcc -nostdlib -L"D:\NXP\BP\lpc_chip_15xx\Debug" -L"D:\NXP\BP\lpc_board_nxp_lpcxpresso_1549\Debug" -Xlinker -Map="periph_rtc.map" -Xlinker --gc-sections -mcpu=cortex-m3 -mthumb -T periph_rtc_Debug.ld -o "periph_rtc.axf" $(OBJS) $(USER_OBJS) $(LIBS) -llpc_board_nxp_lpcxpresso_1549 -llpc_chip_15xx
	@echo 'Finished building target: $@'
	@echo ' '

# Other Targets
clean:
	-$(RM) periph_rtc.axf
	-@echo ' '

post-build:
	-@echo 'Performing post-build steps'
	-arm-none-eabi-size "periph_rtc.axf"; # arm-none-eabi-objcopy -v -O binary "periph_rtc.axf" "periph_rtc.bin" ; # checksum -p LPC1549 -d "periph_rtc.bin";
	-@echo ' '

.PHONY: all clean dependents main-build post-build

-include ../makefile.targets
