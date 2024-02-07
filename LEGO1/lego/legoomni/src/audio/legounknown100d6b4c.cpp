#include "legounknown100d6b4c.h"

DECOMP_SIZE_ASSERT(LegoUnknown100d6b4c, 0x20);

// Inline constructor at 0x10029adb
LegoUnknown100d6b4c::LegoUnknown100d6b4c()
{
	// TODO
}

// STUB: LEGO1 0x1003cf20
LegoUnknown100d6b4c::~LegoUnknown100d6b4c()
{
	// TODO
}

// FUNCTION: LEGO1 0x1003d050
MxResult LegoUnknown100d6b4c::Tickle()
{
	// Map100d6b4c::iterator it;
	for (Map100d6b4c::iterator it = m_map.begin(); it != m_map.end(); it++) {
		LegoCacheSound*& sound = (*it).second;
		if (sound->GetUnk0x58()) {
			sound->FUN_10006be0();
		}
	}

	for (it = m_map.begin(); it != m_map.end(); it++) {
		LegoCacheSound*& sound = (*it).second;
		if (sound->GetUnk0x58()) {
			sound->FUN_10006be0();
		}
		sound->FUN_10006b80();
	}

	return SUCCESS;
}

// STUB: LEGO1 0x1003dc40
void LegoUnknown100d6b4c::FUN_1003dc40(LegoCacheSound** p_und)
{
	// TODO
}
