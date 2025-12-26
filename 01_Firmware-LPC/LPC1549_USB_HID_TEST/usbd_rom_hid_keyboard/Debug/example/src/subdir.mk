################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../example/src/cr_startup_lpc15xx.c \
../example/src/hid_desc.c \
../example/src/hid_keyboard.c \
../example/src/hid_main.c \
../example/src/ms_timer.c \
../example/src/sysinit.c 

C_DEPS += \
./example/src/cr_startup_lpc15xx.d \
./example/src/hid_desc.d \
./example/src/hid_keyboard.d \
./example/src/hid_main.d \
./example/src/ms_timer.d \
./example/src/sysinit.d 

OBJS += \
./example/src/cr_startup_lpc15xx.o \
./example/src/hid_desc.o \
./example/src/hid_keyboard.o \
./example/src/hid_main.o \
./example/src/ms_timer.o \
./example/src/sysinit.o 


# Each subdirectory must supply rules for building sources it contributes
example/src/%.o: ../example/src/%.c example/src/subdir.mk
	@echo 'Building file: $<'
	@echo 'Invoking: MCU C Compiler'
	arm-none-eabi-gcc -DDEBUG -D__CODE_RED -D__USE_LPCOPEN -D__REDLIB__ -DCORE_M3 -I"D:\NXP\BP\LPC1549_USB_HID\lpc_chip_15xx\inc" -I"D:\NXP\BP\LPC1549_USB_HID\lpc_board_nxp_lpcxpresso_1549\inc" -I"D:\NXP\BP\LPC1549_USB_HID\usbd_rom_hid_keyboard\example\inc" -I"D:\NXP\BP\LPC1549_USB_HID\lpc_chip_15xx\inc\usbd" -O0 -g3 -gdwarf-4 -Wall -c -fmessage-length=0 -fno-builtin -ffunction-sections -fdata-sections -fmerge-constants -fmacro-prefix-map="$(<D)/"= -mcpu=cortex-m3 -mthumb -fstack-usage -specs=redlib.specs -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.o)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


clean: clean-example-2f-src

clean-example-2f-src:
	-$(RM) ./example/src/cr_startup_lpc15xx.d ./example/src/cr_startup_lpc15xx.o ./example/src/hid_desc.d ./example/src/hid_desc.o ./example/src/hid_keyboard.d ./example/src/hid_keyboard.o ./example/src/hid_main.d ./example/src/hid_main.o ./example/src/ms_timer.d ./example/src/ms_timer.o ./example/src/sysinit.d ./example/src/sysinit.o

.PHONY: clean-example-2f-src

