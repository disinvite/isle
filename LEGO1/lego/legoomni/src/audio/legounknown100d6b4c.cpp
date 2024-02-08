#include "legounknown100d6b4c.h"

#include "legoomni.h"
#include "legoworld.h"

DECOMP_SIZE_ASSERT(LegoUnknown100d6b4c, 0x20);

/*
// Inline constructor at 0x10029adb
LegoUnknown100d6b4c::LegoUnknown100d6b4c()
{
	// TODO
}
*/

// FUNCTION: LEGO1 0x1003cf20
LegoUnknown100d6b4c::~LegoUnknown100d6b4c()
{
	// TODO
	m_list.clear();
}

// FUNCTION: LEGO1 0x1003d050
MxResult LegoUnknown100d6b4c::Tickle()
{
	for (Map100d6b4c::iterator map_it = m_map.begin(); map_it != m_map.end(); map_it++) {
		LegoCacheSound* sound = (*map_it).m_sound;
		if (sound->GetUnk0x58()) {
			sound->FUN_10006be0();
		}
	}

	List100d6b4c::iterator list_it = m_list.begin();
	while (list_it != m_list.end()) {
		LegoCacheSound* sound = (*list_it).m_sound;
		if (sound->GetUnk0x58()) {
			sound->FUN_10006be0();
			list_it++;
			continue;
		}
		sound->FUN_10006b80();

		List100d6b4c::iterator temp = list_it;
		list_it++;

		m_list.erase(temp);
		delete sound;
	}

	return SUCCESS;
}

// STUB: LEGO1 0x1003d170
void LegoUnknown100d6b4c::FUN_1003d170(const char* p_key)
{
	// TODO
	// const char* x = strcpy(p_key);
}

// FUNCTION: LEGO1 0x1003d290
LegoCacheSound* LegoUnknown100d6b4c::FUN_1003d290(LegoCacheSound* p_sound)
{
	Map100d6b4c::iterator it = m_map.find(Element1006b4c(p_sound));

	// TODO

	if (p_sound->GetUnk0x58()) {
		m_list.push_back(Element1006b4c(p_sound, p_sound->GetString0x48().GetData()));
	}
	else {
		LegoWorld* world = CurrentWorld();
		if (world) {
			world->Add(p_sound);
		}
	}

	return p_sound;
}

// STUB: LEGO1 0x1003dc40
void LegoUnknown100d6b4c::FUN_1003dc40(LegoCacheSound** p_und)
{
	// TODO
}
