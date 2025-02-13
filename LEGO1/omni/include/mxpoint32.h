#ifndef MXPOINT32_H
#define MXPOINT32_H

#include "mxgeometry.h"
#include "mxtypes.h"

class MxPoint32 : public MxPoint<MxS32> {
public:
	// FUNCTION: BETA10 0x10054d10
	MxPoint32() {}

	// FUNCTION: LEGO1 0x10012170
	// FUNCTION: BETA10 0x10031a50
	MxPoint32(const MxPoint32& p_p) : MxPoint<MxS32>(p_p) {}

	// FUNCTION: BETA10 0x1006aa70
	MxPoint32(MxS32 p_x, MxS32 p_y) : MxPoint<MxS32>(p_x, p_y) {}
};

// TEMPLATE: BETA10 0x10031a80
// ??0?$MxPoint@H@@QAE@ABV0@@Z

// TEMPLATE: BETA10 0x100318f0
// MxPoint<int>::GetX

// TEMPLATE: BETA10 0x10031920
// MxPoint<int>::GetY

// TEMPLATE: BETA10 0x10031cf0
// ??0?$MxPoint@H@@QAE@HH@Z

// TEMPLATE: BETA10 0x10054d40
// ??0?$MxPoint@H@@QAE@XZ

// TEMPLATE: BETA10 0x10142c90
// MxPoint32::SetX

// TEMPLATE: BETA10 0x10142cb0
// MxPoint32::SetY

#endif // MXPOINT32_H
