#include "legounknown100d5778.h"

#include "legoomni.h"
#include "legounksavedatawriter.h"

DECOMP_SIZE_ASSERT(LegoUnknown100d5778, 0x30);

// FUNCTION: LEGO1 0x10011630
LegoUnknown100d5778::LegoUnknown100d5778()
{
	Init();
}

// FUNCTION: LEGO1 0x10011670
LegoUnknown100d5778::~LegoUnknown100d5778()
{
	FUN_10011880();
}

// FUNCTION: LEGO1 0x10011680
void LegoUnknown100d5778::Init()
{
	m_unk0x8 = NULL;
	m_unk0xc = NULL;
	m_unk0x10 = 0;
	m_unk0x18 = 0;
	m_unk0x14 = FALSE;
	m_unk0x15 = FALSE;
	m_unk0x2c = 79;
}

// FUNCTION: LEGO1 0x10011880
void LegoUnknown100d5778::FUN_10011880()
{
	// TODO: I'm not certain this member is LPDIRECTSOUND, but it is something
	// from dsound.h. They all have Release() as vtable+0x8.
	if (m_unk0x8) {
		m_unk0x8->Release();
		m_unk0x8 = NULL;
	}

	if (m_unk0x14 && m_unk0xc && UnkSaveDataWriter()) {
		if (m_unk0x15) {
			UnkSaveDataWriter()->FUN_10083db0(m_unk0xc);
		}
		else {
			UnkSaveDataWriter()->FUN_10083f10(m_unk0xc);
		}
	}

	Init();
}
