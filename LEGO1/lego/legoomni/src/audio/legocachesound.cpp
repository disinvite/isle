#include "legocachesound.h"

DECOMP_SIZE_ASSERT(LegoCacheSound, 0x88)

// FUNCTION: LEGO1 0x100064d0
LegoCacheSound::LegoCacheSound()
{
	Init();
}

// STUB: LEGO1 0x10006630
LegoCacheSound::~LegoCacheSound()
{
	// TODO
}

// FUNCTION: LEGO1 0x100066d0
void LegoCacheSound::Init()
{
	m_unk0x8 = 0;
	m_unk0x40 = 0;
	m_unk0x58 = 0;
	memset(&m_unk0x59, 0, sizeof(m_unk0x59));
	m_unk0x6a = 0;
	m_unk0x70 = 0;
	m_unk0x69 = 1;
	m_unk0x6c = 79;
	m_unk0x84 = 0;
}

// STUB: LEGO1 0x10006b80
void LegoCacheSound::FUN_10006b80()
{
	// TODO
}

// STUB: LEGO1 0x10006be0
void LegoCacheSound::FUN_10006be0()
{
	// TODO
}
