#ifndef LEGOUNKNOWN100D6B4C_H
#define LEGOUNKNOWN100D6B4C_H

#include "decomp.h"
#include "legocachesound.h"
#include "mxstl/stlcompat.h"
#include "mxtypes.h"

struct Map100d6b4cComparator {
	bool operator()(const char* const& p_key0, const char* const& p_key1) const { return strcmpi(p_key0, p_key1) > 0; }
};

// set of pair?
typedef map<char*, LegoCacheSound*, Map100d6b4cComparator> Map100d6b4c;

// VTABLE: LEGO1 0x100d6b4c
// SIZE 0x20
class LegoUnknown100d6b4c {
public:
	LegoUnknown100d6b4c();
	~LegoUnknown100d6b4c();

	virtual MxResult Tickle(); // vtable+0x00

	void FUN_1003dc40(LegoCacheSound** p_und);

private:
	Map100d6b4c m_map;
	undefined m_pad[0xc];
};

#endif // LEGOUNKNOWN100D6B4C_H
