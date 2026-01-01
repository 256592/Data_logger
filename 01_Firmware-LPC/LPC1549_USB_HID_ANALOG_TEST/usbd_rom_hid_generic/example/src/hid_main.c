#include "board.h"
#include <stdio.h>
#include <string.h>
#include "app_usbd_cfg.h"
#include "hid_generic.h"

// dopsat VID - idVendor, PID - idProduct v hid_desc.c
// pridat cislovani paketu do pc_out_report, aby se nezpracovaly dvakrat
// CH-01: PIO0_8, ADC0_0
// CH-02: PIO0_7, ADC0_1

#define USER_LED	12

static USBD_HANDLE_T g_hUsb;
static bool sequence0Complete;

const  USBD_API_T *g_pUsbApi;
static volatile int ticks;
volatile uint32_t casovac1ms, casovac1s;

// --- USB---
uint8_t pc_out_report[64];
uint8_t pc_in_report[64];

// ---ADC---
uint16_t analog_val;

// ---logger vars--
uint8_t log_period = 10;

// Handle interrupt from USB
void USB_IRQHandler(void)
{
	USBD_API->hw->ISR(g_hUsb);
}

/* Find the address of interface descriptor for given class type. */
USB_INTERFACE_DESCRIPTOR *find_IntfDesc(const uint8_t *pDesc, uint32_t intfClass)
{
	USB_COMMON_DESCRIPTOR *pD;
	USB_INTERFACE_DESCRIPTOR *pIntfDesc = 0;
	uint32_t next_desc_adr;

	pD = (USB_COMMON_DESCRIPTOR *) pDesc;
	next_desc_adr = (uint32_t) pDesc;

	while (pD->bLength) {
		/* is it interface descriptor */
		if (pD->bDescriptorType == USB_INTERFACE_DESCRIPTOR_TYPE) {

			pIntfDesc = (USB_INTERFACE_DESCRIPTOR *) pD;
			/* did we find the right interface descriptor */
			if (pIntfDesc->bInterfaceClass == intfClass) {
				break;
			}
		}
		pIntfDesc = 0;
		next_desc_adr = (uint32_t) pD + pD->bLength;
		pD = (USB_COMMON_DESCRIPTOR *) next_desc_adr;
	}
	return pIntfDesc;
}



int main(void)
{
	USBD_API_INIT_PARAM_T usb_param;
	USB_CORE_DESCS_T desc;
	ErrorCode_t ret = LPC_OK;

	SystemCoreClockUpdate();
	LPC_SYSCON->SYSAHBCLKCTRL[0] |= (1<<11) | (1<<12) | (1<<13) | (1<<14) | (1<<16) | (1<<9);
	Board_Init();

	// --- ADC init ---
	LPC_SWM->PINENABLE[0] &= ~(1<<0);	// ADC0-0
	LPC_SWM->PINENABLE[0] &= ~(1<<1);	// ADC0-1
	LPC_IOCON->PIO[0][8] = 0;			// PIN 8
	LPC_IOCON->PIO[0][7] = 0;			// PIN 7

	Chip_ADC_Init(LPC_ADC0, 0);			//Setup ADC for 12-bit mode and normal power
	Chip_ADC_SetClockRate(LPC_ADC0, ADC_MAX_SAMPLE_RATE/16);			//Setup for maximum ADC clock rate
	Chip_ADC_SetSequencerBits(LPC_ADC0, ADC_SEQA_IDX, (1<<1) | (1<<0));
	Chip_ADC_SetSequencerBits(LPC_ADC0, ADC_SEQA_IDX, ADC_SEQ_CTRL_SEQ_ENA);
	Chip_ADC_SetSequencerBits(LPC_ADC0, ADC_SEQA_IDX, ADC_SEQ_CTRL_BURST);

	/* enable clocks */
	Chip_USB_Init();
	/* initialize USBD ROM API pointer. */
	g_pUsbApi = (const USBD_API_T *) LPC_ROM_API->pUSBD;
	/* initialize call back structures */
	memset((void *) &usb_param, 0, sizeof(USBD_API_INIT_PARAM_T));
	usb_param.usb_reg_base = LPC_USB0_BASE;
	usb_param.max_num_ep = 2 + 1;
	usb_param.mem_base = USB_STACK_MEM_BASE;
	usb_param.mem_size = USB_STACK_MEM_SIZE;
	/* Set the USB descriptors */
	desc.device_desc = (uint8_t *) USB_DeviceDescriptor;
	desc.string_desc = (uint8_t *) USB_StringDescriptor;
	desc.high_speed_desc = USB_FsConfigDescriptor;
	desc.full_speed_desc = USB_FsConfigDescriptor;
	desc.device_qualifier = 0;

	/* USB Initialization */
	ret = USBD_API->hw->Init(&g_hUsb, &desc, &usb_param);
	if (ret == LPC_OK) {

		ret =
			usb_hid_init(g_hUsb,
						 (USB_INTERFACE_DESCRIPTOR *) &USB_FsConfigDescriptor[sizeof(USB_CONFIGURATION_DESCRIPTOR)],
						 &usb_param.mem_base, &usb_param.mem_size);
		if (ret == LPC_OK) {
			/*  enable USB interrupts */
			NVIC_EnableIRQ(USB0_IRQn);
			/* now connect */
			USBD_API->hw->Connect(g_hUsb, 1);
		}
	}

	// --- preruseni---
	Chip_RIT_Init(LPC_RITIMER);
    Chip_RIT_SetTimerIntervalHz(LPC_RITIMER,1000);
    LPC_RITIMER->CTRL = (1<<1) | (1<<3);
    //nejnizsi priorita na cyklicke preruseni,
    NVIC_SetPriority(RITIMER_IRQn, 7);
    NVIC_EnableIRQ(RITIMER_IRQn);
    Chip_SCT_Init(LPC_SCT0);
    // nastaveni gpio a swm
    LPC_GPIO->DIR[0] |= (1<<USER_LED);
    //LPC_GPIO->DIR[0] &= ~(1<<CH01);
    LPC_SWM->PINASSIGN[7] = 0xffffffff;

    //LPC_GPIO->SET[0] = 1 << USER_LED;

    _Bool auto_logging, manual_logging;

    auto_logging = false;
    manual_logging = false;
    pc_in_report[0] = 10;

    while(1)
    {
    	analog_val = (Chip_ADC_GetDataReg(LPC_ADC0,0) >> 4) & 0xfff;
    	// analog_val = (Chip_ADC_GetDataReg(LPC_ADC0,1) >> 4) & 0xfff;

    	pc_in_report[0] = analog_val;
    	pc_in_report[1] = (analog_val >> 8);


    	if (pc_out_report[0] & (1 << 0))	// 1 na nultem bitu - auto rezim
    	{
    	    log_period = pc_out_report[1] + 1;

    	    if (casovac1s >= log_period)
    	    {
    	        LPC_GPIO->SET[0] = 1 << USER_LED;
    	        casovac1s = 0;
    	        USBD_API->hw->WriteEP(g_hUsb,HID_EP_IN , pc_in_report, 64);
    	    }
    	     if (casovac1ms == 50)
    	        LPC_GPIO->CLR[0] = 1 << USER_LED;
    	}

    	if (pc_out_report[0] & (1 << 1))	// 1 na prvnim bitu - manual rezim
    	{
    		USBD_API->hw->WriteEP(g_hUsb,HID_EP_IN , pc_in_report, 64);
    		pc_out_report[0] = 0;
    	}
    }
}

void RIT_IRQHandler(void) {
	LPC_RITIMER->CTRL |= 1; //zruseni priznaku preruseni
	casovac1ms++; //casovac 1 ms
	if (casovac1ms == 1000)
	{
		casovac1s++;
		casovac1ms = 0;
	}
}

